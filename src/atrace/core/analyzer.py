from dataclasses import dataclass
from itertools import groupby
from operator import itemgetter
from typing import Any, TypeAlias

from .tracer import (
    Call,
    Line,
    Loc,
    Output,
    Return,
    Symbols,
    Trace,
)

""""
Takes a raw trace makes sense of it:
    - Detects variable assignments and the line where they occurred
    - Coalesces subsequent outputs that happen on the same line together
"""


@dataclass(frozen=True)
class Var:
    scope: str
    name: str


UNASSIGN = object()

Assignments: TypeAlias = dict[Var, Any]

UnpackedHistory: TypeAlias = list[tuple[Loc, Assignments | str]]

History: TypeAlias = list[tuple[Loc, Assignments, str | None]]


@dataclass
class Activation:
    locals: Symbols
    last_loc: Loc


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


def _trace_to_unpacked_history(trace: Trace) -> UnpackedHistory:
    """
    Simulate the state of global and local symbols,
    in order to reconstruct a history of assignments.

    Because line events are emitted _before_ a line is executed,
    we only see the new values of globals and locals when the next event arrives.
    """
    history: UnpackedHistory = []

    current_globals: Symbols = {}
    activations = [Activation({}, Loc("guard", 0))]

    for loc, event in trace:
        match event:
            case Call(_, locals):
                activations.append(Activation(locals, loc))
                # Capture the function bindings,
                local_assignments = diff(loc.function_name, {}, locals)
                history.append((loc, local_assignments))

            case Line(globals, locals) | Return(globals, locals):
                activation = activations[-1]
                local_assignments = diff(loc.function_name, activation.locals, locals)
                global_assignments = diff("<module>", current_globals, globals)
                assignments = local_assignments | global_assignments

                history.append((activation.last_loc, assignments))

                activation.locals = locals
                current_globals = globals
                if isinstance(event, Line):
                    activation.last_loc = loc
                elif isinstance(event, Return):
                    activations.pop()

            case Output(text):
                history.append((loc, text))

    return history


def _join_outputs(unpacked: UnpackedHistory) -> History:
    """
    Coalesce consecutive events that occur on the same line: outputs, assignments
    """
    joined = []
    for loc, group in groupby(unpacked, key=itemgetter(0)):
        pending_output = None
        for _, item in group:
            match item:
                case str(text):
                    pending_output = (pending_output or "") + text
                case _ as assignments:
                    joined.append((loc, assignments, pending_output))
                    pending_output = None
        if pending_output:
            joined.append((loc, {}, pending_output))

    return joined

def _filter_zero_lines(unfiltered: History) -> History:
    """ An artefact of tracing is seeing events that happen before line 1 of the program is executed """
    return [
        (loc, assignments, output)
        for loc, assignments, output in unfiltered
        if loc.line_no != 0
    ]


def _filter_no_effect(unfiltered:History) -> History:
    """" Remove history items that neither assign nor output """
    return [
        (loc, assignments, output)
        for loc, assignments, output in unfiltered
        if assignments or output
    ]


def trace_to_history(trace: Trace, keep_no_effect=False) -> History:
    unpacked = _trace_to_unpacked_history(trace)
    joined =  _join_outputs(unpacked)
    cleaned = _filter_zero_lines(joined)
    if keep_no_effect:
        return cleaned
    else:
        return _filter_no_effect(cleaned)
