from dataclasses import dataclass
from itertools import groupby
from operator import itemgetter
from typing import Any, TypeAlias

from .tracer import (
    CallEvent,
    ExecutionEvent,
    LineEvent,
    Loc,
    OutputEvent,
    ReturnEvent,
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

    def __repr__(self):
        return f"""Var("{self.scope}", "{self.name}")"""


Assignments: TypeAlias = dict[Var, Any]

History: TypeAlias = list[tuple[Loc, Assignments, str]]


@dataclass
class Activation:
    locals: Symbols
    last_loc_and_event: tuple[Loc, ExecutionEvent] | None


def diff(scope: str, before: Symbols | None, after: Symbols | None) -> Assignments:
    if not after:
        return {}
    before = before or {}
    assignments = {}
    for var, val in after.items():
        if var not in before or val != before[var]:
            assignments[Var(scope, var)] = val
    return assignments


def trace_to_unpacked_history(trace: Trace) -> History:
    """
    It's important to not try and reduce the history to only eventful lines,
    otherwise it's impossible to group properly. XXX: Explain better
    """
    res = []

    # The globals we see before a line gets executed are unreliable
    # (they can get changed for instance inside a function that the line will invoke)
    # So we simulate the state of the program with this variable
    current_globals: Symbols = {}
    activations = [Activation({}, None)]

    for loc, event in trace:
        match event:
            case CallEvent(_, locals):
                activations.append(Activation(locals, (loc, event)))
                # Capture the function bindings,
                local_assignments = diff(loc.function_name, {}, locals)
                res.append((loc, local_assignments, ""))

            case LineEvent(globals, locals) | ReturnEvent(globals, locals):
                activation = activations[-1]
                target = activation.last_loc_and_event
                if target:
                    target_loc, target_event = target
                    local_assignments = diff(
                        loc.function_name, activation.locals, locals
                    )
                    global_assignments = diff("<module>", current_globals, globals)
                    assignments = local_assignments | global_assignments

                    res.append((target_loc, assignments, ""))

                    activation.locals = locals
                    current_globals = globals
                if isinstance(event, LineEvent):
                    activations[-1].last_loc_and_event = (loc, event)
                elif isinstance(event, ReturnEvent):
                    activations.pop()
                res.append((loc, {}, ""))  # XXX

            case OutputEvent(text):
                res.append((loc, {}, text))

    return res


def pack_history(unpacked: History) -> History:
    """
    - Coalesce consecutive events that occur on the same line: outputs, assignments
    - Remove history items that neither assign nor output
    """
    res = []
    # Group consecutive items by the first element (loc)
    for loc, group in groupby(unpacked, key=itemgetter(0)):
        # Unpack the first item to get starting assignments and output
        _, assignments, output = next(group)

        # Unpack subsequent items in the group to merge their output
        for _, new_assignments, new_output in group:
            assignments = assignments | new_assignments
            output = output + new_output

        if assignments or output:
            res.append((loc, assignments, output))

    return res


def trace_to_history(trace: Trace) -> History:
    unpacked = trace_to_unpacked_history(trace)
    return pack_history(unpacked)
