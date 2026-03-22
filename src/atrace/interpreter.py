from collections.abc import Generator
from dataclasses import dataclass
from itertools import groupby
from types import TracebackType
from typing import Any, NamedTuple, TypeAlias

from . import Symbols, TCall, TException, TLine, TOutput, Trace, TReturn

"""
Takes a raw trace to make sense of it:
- Assigns variable assignments and outputs to the line where they occurred
- Coalesces effects that happen on the same line together

The result of this phase is a History
"""


class Var(NamedTuple):
    scope: str
    name: str


class Unassign:
    def __repr__(self):
        return "<UNASSIGN>"


UNASSIGN = Unassign()
Assignments: TypeAlias = dict[Var, Any]


def diff(scope: str, before: Symbols, after: Symbols) -> Assignments:
    assignments = {}

    # New variables or changes
    for var, val in after.items():
        if var not in before or val != before[var]:
            assignments[Var(scope, var)] = val

    # Variables that were unassigned
    for unassigned in before.keys() - after.keys():
        assignments[Var(scope, unassigned)] = UNASSIGN

    return assignments


class Call(NamedTuple):
    function_name: str
    bindings: Assignments


class Return(NamedTuple):
    return_value: Any


class Raise(NamedTuple):
    type: type
    value: Exception
    traceback: TracebackType


class Line(NamedTuple):
    pass


class LineEffects(NamedTuple):
    assignments: Assignments
    output: str | None


HistoryItem: TypeAlias = tuple[int, Line | LineEffects | Call | Return | Raise]
History: TypeAlias = list[HistoryItem]


@dataclass
class Activation:
    function_name: str
    locals: Symbols
    last_line_no: int


def _trace_to_unpacked_history(trace: Trace) -> Generator[HistoryItem]:
    """Simulate the state of global and local symbols in order to reconstruct
    a history of assignments.

    Because line events are emitted _before_ a line is executed,
    we only see the new values of globals and locals when the next event arrives.
    """

    current_globals: Symbols = {}
    activations = [Activation("guard", {}, -1)]

    for lineno, event in trace:

        def _compute_assignments(activation: Activation, globs: Symbols, locs: Symbols):
            local_assignments = diff(activation.function_name, activation.locals, locs)
            global_assignments = diff("<module>", current_globals, globs)
            return local_assignments | global_assignments

        match event:
            case TCall(_, locs, function_name):
                activations.append(Activation(function_name, locs, -1))
                function_bindings = diff(function_name, {}, locs)
                yield lineno, Call(function_name, function_bindings)

            case TLine(globs, locs):
                activation = activations[-1]
                a = _compute_assignments(activation, globs, locs)
                if a:
                    yield activation.last_line_no, LineEffects(a, None)

                yield lineno, Line()
                current_globals = globs
                activation.locals = locs
                activation.last_line_no = lineno

            case TReturn(globs, locs, return_value):
                activation = activations[-1]
                a = _compute_assignments(activation, globs, locs)
                if a:
                    yield activation.last_line_no, LineEffects(a, None)

                current_globals = globs
                yield lineno, Return(return_value)
                activations.pop()

            case TException(globs, locs, _exception, value, traceback):
                activation = activations[-1]
                a = _compute_assignments(activation, globs, locs)
                if a:
                    yield activation.last_line_no, LineEffects(a, None)

                current_globals = globs
                yield lineno, Raise(_exception, value, traceback)

            case TOutput(text):
                activation = activations[-1]
                yield activation.last_line_no, LineEffects({}, text)


def _pack_effects(unpacked: Generator[HistoryItem]) -> Generator[HistoryItem]:
    """Merge consecutive LineEffects together."""
    for (lineno, is_effects), group in groupby(
        unpacked, key=lambda x: (x[0], isinstance(x[1], LineEffects))
    ):
        if is_effects:
            assignments: Assignments = {}
            outputs: list[str] = []

            for _, line_effects in group:
                assert isinstance(line_effects, LineEffects)  # for mypy
                assignments |= line_effects.assignments
                if line_effects.output is not None:
                    outputs.append(line_effects.output)

            yield lineno, LineEffects(assignments, "".join(outputs) or None)
        else:
            yield from group


def _filter_artifacts(history: History) -> History:
    """Remove implementation artifacts from History:
    - It always contains an extra return at the end that's not part of our program.
      We get rid of that
    - Depending on how the trace was captured it sometimes starts with a call into the
      module with lineno 0. We get rid of that as well.
    """

    if len(history) < 2:
        return history

    lineno, _ = history[0]
    if lineno == 0:
        return history[1:-1]
    else:
        return history[:-1]


def trace_to_history(trace: Trace) -> History:
    """Build a History by interpreting the trace."""
    unpacked = _trace_to_unpacked_history(trace)
    packed = _pack_effects(unpacked)
    return _filter_artifacts(list(packed))
