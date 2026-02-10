from dataclasses import dataclass
from functools import pairwise
from typing import Any, TypeAlias

from .vartracer import OutputEvent, Trace

""""
Takes a raw trace and:
    - Coalesces output events
    - Assigns the variable changes where they occur (in the raw trace we see changes after the face)
    - Removes unnecessary events
- """


@dataclass
class Assignment:
    line_no: int
    function_name: str
    variables: dict[str, Any]


Assignments: TypeAlias = list[Assignment]


@dataclass
class Output:
    line_no: int
    function_name: str
    text: str


Outputs: TypeAlias = list[Output]



def extract_and_coalesce_outputs(trace: Trace) -> tuple[Outputs, Trace]:
    outputs = []
    execution_events = []
    pending = None
    for traceItem in trace:
        match traceItem.event:
            case OutputEvent(text):
                if pending and pending.line_no == traceItem.line_no:
                    pending.text += text
                else:
                    pending = Output(
                        line_no=traceItem.line_no,
                        function_name=traceItem.function_name,
                        text=text,
                    )
            case _:
                execution_events.append(traceItem)
                if pending:
                    outputs.append(pending)
                    pending = None
    if pending:
        outputs.append(pending)

    return outputs, execution_events


def execution_events_to_assignments(trace: Trace) -> Assignments:
    result = []
    for item, next in pairwise(trace):
        if var not in item.locals or old_locals[var] != new_val:
        pass
    return result


def fixup(trace: Trace) -> tuple[Assignments, Outputs]:
    outputs, execution_events = extract_and_coalesce_outputs(trace)
    assignments = execution_events_to_assignments(execution_events)
    return assignments, outputs
