import copy
import sys
from dataclasses import dataclass
from types import FrameType, ModuleType, TracebackType
from typing import Any, Callable, TextIO, TypeAlias

"""
See:
    https://docs.python.org/3/library/sys.html#sys.settrace
"""


@dataclass(frozen=True)
class Loc:
    function_name: str
    line_no: int


Symbols: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class ExecutionEvent:
    globals: Symbols
    locals: Symbols


@dataclass(frozen=True)
class Line(ExecutionEvent):
    """
    The interpreter is about to execute a new line of code or re-execute the condition of a loop
    """


@dataclass(frozen=True)
class Call(ExecutionEvent):
    """
    A function is called or some other code block entered.
    This is emitted before entering the function (in most cases this is on the line of the function def)
    One can already see:
        - The function name
        - The bound parameters
    """


@dataclass(frozen=True)
class Return(ExecutionEvent):
    """
    A function or other code block is about to return.
    """

    return_value: Any


@dataclass(frozen=True)
class ExceptionOccured(ExecutionEvent):
    """
    An exception has occurred
    """

    exception: Exception
    value: Any
    traceback: TracebackType


@dataclass(frozen=True)
class Output:
    """
    Some text was written to stdout
    """

    text: str


Event: TypeAlias = Line | Call | Return | ExceptionOccured | Output

Trace: TypeAlias = list[tuple[Loc, Event]]

DoneCallback = Callable[[Trace], None]


def ignore_variable(name: str, value: Any) -> bool:
    return name.startswith("__") or callable(value) or isinstance(value, ModuleType)


def filtered_variables(variables: dict[str, Any]) -> dict[str, Any]:
    return {
        name: value
        for name, value in variables.items()
        if not ignore_variable(name, value)
    }


def ignore_function(name: str) -> bool:
    return name.startswith("__")


def copy_carefully(symbols: Symbols) -> Symbols:
    """
    In order to capture mutations to values, we try to deepcopy them at each step.
    If we cannot deepcopy an item, we revert to just referencing it:
    - The program doesn't break
    - We may not be able to see some mutations.
    """
    res = {}
    for k, v in symbols.items():
        try:
            v_copy = copy.deepcopy(v)
        except (copy.Error, TypeError):
            v_copy = v
        res[k] = v_copy
    return res


class OutputLogger:
    """
    OutputLogger wraps stdout.
    It passes down writes and flushes to it, while simultaneously capturing the text to the trace.
    """

    def __init__(self, trace: Trace, stdout: TextIO):
        self.trace = trace
        self.stdout = stdout

    def write(self, text: str) -> None:
        """
        Write to stdout and also record the text in the trace
        """
        self.stdout.write(text)

        frame = sys._getframe(1)

        self.trace.append((Loc(frame.f_code.co_name, frame.f_lineno), Output(text)))

    def flush(self):
        self.stdout.flush()


CONAME = "<module>"


class Tracer:
    def __init__(
        self, done_callback: DoneCallback, attached_to_frame: FrameType | None
    ):
        self.done_callback = done_callback
        self.attached_to_frame = attached_to_frame
        self.trace: Trace = []
        self.original_stdout = sys.stdout
        self.filename_of_interest: str | None = None

        sys.settrace(self.trace_vars)
        if attached_to_frame:
            attached_to_frame.f_trace = self.trace_vars

    def trace_vars(self, frame: FrameType, event: str, arg: Any):
        if not self.filename_of_interest:
            if frame.f_code.co_name == CONAME:
                # Until now we were lurking, finding out when to start collecting info.
                # It's time to get to work.
                self.filename_of_interest = frame.f_code.co_filename
                sys.stdout = OutputLogger(trace=self.trace, stdout=self.original_stdout)
            else:
                return None

        # We don't want to step out of the file we are tracing
        if frame.f_code.co_filename != self.filename_of_interest:
            return None

        # Some very dynamic environment (such as Thonny) start loading proxies and stuff during our module execution.
        # Don't trace those.
        if ignore_function(frame.f_code.co_name):
            return None

        globals = copy_carefully(filtered_variables(frame.f_globals))
        if frame.f_locals is frame.f_globals:
            locals = {}
        else:
            locals = copy_carefully(filtered_variables(frame.f_locals))

        trace_event: Event | None = None
        match event:
            case "line":
                trace_event = Line(globals=globals, locals=locals)
            case "call":
                trace_event = Call(globals=globals, locals=locals)
            case "return":
                trace_event = Return(globals=globals, locals=locals, return_value=arg)
            case "exception":
                trace_event = ExceptionOccured(
                    globals=globals,
                    locals=locals,
                    exception=arg[0],
                    value=arg[1],
                    traceback=arg[2],
                )
            case _:
                pass

        if trace_event:
            self.trace.append((Loc(frame.f_code.co_name, frame.f_lineno), trace_event))

        # Detect if we are leaving the module we wanted to trace.
        # Unload if the job is done.
        if (
            event == "return"
            and frame.f_code.co_filename == self.filename_of_interest
            and frame.f_code.co_name == CONAME
        ):
            self.unload()
            return None

        return self.trace_vars

    def unload(self):
        sys.settrace(None)
        if self.attached_to_frame:
            self.attached_to_frame.f_trace = None
        sys.stdout = self.original_stdout
        self.done_callback(self.trace)
