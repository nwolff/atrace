import copy
import sys
from dataclasses import dataclass
from types import FrameType, ModuleType, TracebackType
from typing import Any, TypeAlias

"""
See:
    https://docs.python.org/3/library/sys.html#sys.settrace
    https://docs.python.org/3/library/inspect.html
"""


@dataclass(frozen=True)
class ExecutionEvent:
    locals: dict[str, Any]


@dataclass(frozen=True)
class LineEvent(ExecutionEvent):
    """
    The interpreter is about to execute a new line of code or re-execute the condition of a loop
    """


@dataclass(frozen=True)
class CallEvent(ExecutionEvent):
    """
    A function is called (or some other code block entered).
    This is emitted before entering the function (in most cases this is on the line of the function def)
    One can already see:
        - The function name
        - The bound parameters
    """


@dataclass(frozen=True)
class ReturnEvent(ExecutionEvent):
    """
    A function (or other code block) is about to return.
    """

    return_value: Any


@dataclass(frozen=True)
class ExceptionEvent(ExecutionEvent):
    """
    An exception has occured
    """

    exception: Exception
    value: Any
    traceback: TracebackType


@dataclass(frozen=True)
class OutputEvent:
    """
    Some text was written to stdout
    """

    text: str


@dataclass(frozen=True)
class TraceItem:
    line_no: int
    function_name: str
    event: LineEvent | CallEvent | ReturnEvent | ExceptionEvent | OutputEvent


Trace: TypeAlias = list[TraceItem]


def ignore_variable(name: str, value: Any):
    return name.startswith("__") or callable(value) or isinstance(value, ModuleType)


def filtered_variables(variables: dict[str, Any]) -> dict[str, Any]:
    return {
        name: value
        for name, value in variables.items()
        if not ignore_variable(name, value)
    }


def copy_carefully(d: dict[str, Any]) -> dict[str, Any]:
    res = {}
    for k, v in d.items():
        try:
            v_copy = copy.deepcopy(v)
        except Exception:
            v_copy = v
        res[k] = v_copy
    return res


CONAME = "<module>"


class VarTracer:
    def __init__(self, trace: Trace, attached_to_frame: FrameType | None):
        self.trace = trace
        self.attached_to_frame = attached_to_frame
        self.filename_of_interest: str | None = None

    def trace_vars(self, frame: FrameType, event: str, arg: Any):
        if not self.filename_of_interest:
            if frame.f_code.co_name == CONAME:
                # self.first_frame_of_interest = frame
                self.filename_of_interest = frame.f_code.co_filename
            else:
                return

        if frame.f_code.co_filename != self.filename_of_interest:
            return

        locals = copy_carefully(filtered_variables(frame.f_locals))
        trace_event = None
        match event:
            case "line":
                trace_event = LineEvent(locals=locals)
            case "call":
                trace_event = CallEvent(locals=locals)
            case "return":
                trace_event = ReturnEvent(locals=locals, return_value=arg)
            case "exception":
                trace_event = ExceptionEvent(
                    locals=locals, exception=arg[0], value=arg[1], traceback=arg[2]
                )
            case _:
                print("Unexpected event", event)

        if trace_event:
            self.trace.append(
                TraceItem(
                    line_no=frame.f_lineno,
                    function_name=frame.f_code.co_name,
                    event=trace_event,
                )
            )

        # Unload if the job is done.
        # We do this only after recording the return event (for instance for changes to variables that occured the line before)
        if (
            event == "return"
            and frame.f_code.co_filename == self.filename_of_interest
            and frame.f_code.co_name == CONAME
        ):
            self.unload()
            return

        return self.trace_vars  # Not really sure this does anything

    def unload(self):
        sys.settrace(None)
        if self.attached_to_frame:
            self.attached_to_frame.f_trace = None
