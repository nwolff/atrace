import copy
import inspect
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from pprint import pprint
from types import CodeType, FrameType, ModuleType, TracebackType
from typing import Any, NamedTuple, TextIO, TypeAlias

"""
Everything regarding:
- The tracing itself
- The manual and automatic start of tracing

The basic mechanism of python tracing is explained here:
    https://docs.python.org/3/library/sys.html#sys.settrace
"""

try:
    from ._version import __version__  # noqa
except ImportError:
    # Fallback for local development if _version.py hasn't been generated yet
    __version__ = "0.0.0.dev0"


###############################################################################
# DEBUG support
###############################################################################


# Set `DEBUG` in the environment to enable debug logs (extremely verbose)
DEBUG = "DEBUG" in os.environ


def debug_heading(heading):
    """Output a highlighted diagnostic text to stderr if DEBUG is enabled."""
    debug(f"\n\033[93m[{heading.upper()}]\033[0m")


def debug(*args, **kwargs):
    """Output a formatted diagnostic message to stderr if DEBUG is enabled."""
    if DEBUG:
        print(*args, file=sys.stderr, **kwargs)


def debug_pprint(o):
    """Output a pretty printed object if DEBUG is enabled."""
    if DEBUG:
        pprint(o, stream=sys.stderr)


def debug_frame(frame):
    """Log a scrubbed frame dump to stderr if DEBUG is enabled."""
    if not DEBUG:
        return

    attrs = ("f_code", "f_lineno", "f_back", "f_trace", "f_trace_lines")
    frame_info = {a: getattr(frame, a) for a in attrs if hasattr(frame, a)}

    debug(f"<frame at {id(frame):#x}>: ")
    pprint(frame_info, sort_dicts=False, stream=sys.stderr)


def debug_stack_frame():
    """Log the current stack frame to stderr if DEBUG is enabled."""
    if not DEBUG:
        return
    debug("stack frame:")
    pprint(inspect.stack(), stream=sys.stderr)


###############################################################################
# TRACING
###############################################################################
""" The models and classes that collect the trace. """

Symbols: TypeAlias = dict[str, Any]


class TLine(NamedTuple):
    """
    The interpreter is about to execute a new line of code
    or re-execute the condition of a loop
    """

    globals: Symbols
    locals: Symbols


class TCall(NamedTuple):
    """
    A function is called or some other code block entered.
    """

    globals: Symbols
    locals: Symbols
    function_name: str


class TReturn(NamedTuple):
    """
    A function or other code block is about to return.
    """

    globals: Symbols
    locals: Symbols
    return_value: Any


class TException(NamedTuple):
    """
    An exception has occurred
    """

    globals: Symbols
    locals: Symbols
    type: type
    value: Exception
    traceback: TracebackType


class TOutput(NamedTuple):
    """
    Some text was written to stdout
    """

    text: str


TEvent: TypeAlias = TLine | TCall | TReturn | TException | TOutput

Trace: TypeAlias = list[tuple[int, TEvent]]

DoneCallback = Callable[[Trace], None]


def ignore_variable(name: str, value: Any) -> bool:
    return name.startswith("__") or isinstance(value, ModuleType)


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
    OutputLogger wraps stdout. It passes down writes and flushes to it,
    while simultaneously capturing the text to the trace.

    Coalesces consecutive outputs. Because for instance print("hello", "world")
    becomes 4 writes ("hello", " ", "world", "\n")
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
        lineno = frame.f_lineno

        if not self.trace:
            debug_heading("OUTPUT WITH EMPTY TRACE")
            return
        prev_lineno, prev_event = self.trace[-1]
        if prev_lineno == lineno and isinstance(prev_event, TOutput):
            self.trace[-1] = lineno, TOutput(prev_event.text + text)
            return
        self.trace.append((lineno, TOutput(text)))

    def flush(self):
        self.stdout.flush()


BOUNDARY_CONAMES = ("<module>", "<string>")


class TracerState(Enum):
    WAITING = auto()
    TRACING = auto()
    DONE = auto()


TraceFunc: TypeAlias = Callable[[FrameType, str, Any], Any | None]


@dataclass
class Stats:
    start_checks: int = 0
    ignored: int = 0
    captured: int = 0


class Tracer:
    def __init__(
        self, done_callback: DoneCallback, attached_to_frame: FrameType | None
    ):
        debug_heading("TRACER __INIT__")
        debug("param attached_to_frame:", attached_to_frame)
        debug_stack_frame()

        self.stats = Stats()
        self.done_callback = done_callback
        self.attached_to_frame = attached_to_frame
        self.state = TracerState.WAITING
        self.trace: Trace = []
        self.original_stdout = sys.stdout
        self.target_codeobj: CodeType | None = None

        sys.settrace(self.trace_vars)
        if attached_to_frame:
            attached_to_frame.f_trace = self.trace_vars

    def trace_vars(self, frame: FrameType, event: str, arg: Any) -> TraceFunc | None:
        match self.state:
            case TracerState.WAITING:
                self.stats.start_checks += 1
                if self.is_start(frame, event, arg):
                    sys.stdout = OutputLogger(
                        trace=self.trace, stdout=self.original_stdout
                    )
                    self.target_codeobj = frame.f_code
                    self.state = TracerState.TRACING
                    # We start tracing right away
                    self.handle_tracing(frame, event, arg)

            case TracerState.TRACING:
                self.handle_tracing(frame, event, arg)

            case TracerState.DONE:
                debug_heading("RECEIVING EVENTS AFTER DONE")
                debug_frame(frame)

        if self.is_end(frame, event, arg):
            self.unload()
            self.state = TracerState.DONE

        if self.state == TracerState.TRACING and self.is_of_interest(frame, event, arg):
            return self.trace_vars
        else:
            return None

    def is_start(self, frame: FrameType, event: str, arg: Any) -> bool:
        debug_heading("LOOKING FOR START")
        debug(f"event: {event}")
        debug_frame(frame)

        if frame.f_code.co_name in BOUNDARY_CONAMES:
            debug_heading("FOUND START")
            debug(f"because co_name {frame.f_code.co_name} in {BOUNDARY_CONAMES}")
            return True
        else:
            return False

    def handle_tracing(self, frame: FrameType, event: str, arg: Any) -> None:
        if self.is_of_interest(frame, event, arg):
            debug_heading("CAPTURING EVENT")
            debug(f"event: {event}")
            debug_frame(frame)
            self.capture(frame, event, arg)
            self.stats.captured += 1
        else:
            debug_heading("IGNORING EVENT")
            debug(f"event: {event}")
            debug_frame(frame)
            self.stats.ignored += 1

    def capture(self, frame: FrameType, event: str, arg: Any) -> None:
        globs = copy_carefully(filtered_variables(frame.f_globals))
        locs = (
            {}
            if frame.f_locals is frame.f_globals
            else copy_carefully(filtered_variables(frame.f_locals))
        )

        trace_event: TEvent | None = None
        match event:
            case "line":
                trace_event = TLine(globals=globs, locals=locs)
            case "call":
                trace_event = TCall(
                    globals=globs, locals=locs, function_name=frame.f_code.co_name
                )
            case "return":
                trace_event = TReturn(globals=globs, locals=locs, return_value=arg)
            case "exception":
                trace_event = TException(
                    globals=globs,
                    locals=locs,
                    type=arg[0],
                    value=arg[1],
                    traceback=arg[2],
                )
            case _:
                pass

        if trace_event:
            self.trace.append((frame.f_lineno, trace_event))

    def is_of_interest(self, frame: FrameType, event: str, arg: Any) -> bool:
        # We don't want to step out of the file we are tracing
        if (
            self.target_codeobj
            and self.target_codeobj.co_filename != frame.f_code.co_filename
        ):
            return False

        # If we're running from instrumented code, then we ignore frames that were
        # created by __init__.py
        if (
            self.attached_to_frame
            and frame.f_back
            and frame.f_back.f_code.co_filename == __file__
        ):
            return False

        return True

    def is_end(self, frame: FrameType, event: str, arg: Any) -> bool:
        # Detect if we are leaving the module we wanted to trace.
        if event == "return" and frame.f_code == self.target_codeobj:
            debug_heading("FOUND END")
            debug(
                "because: event is return",
                f"and f_code is {self.target_codeobj}",
            )
            debug_frame(frame)
            return True
        else:
            return False

    def unload(self):
        debug_heading("unloading")
        debug(self.stats)
        sys.settrace(None)
        if self.attached_to_frame:
            self.attached_to_frame.f_trace = None
        sys.stdout = self.original_stdout
        self.done_callback(self.trace)


###############################################################################
# Running the trace
###############################################################################


def trace_code(source: str, done_callback: DoneCallback) -> None:
    """Generates a trace from Python source code.

    The callback architecture ensures that the trace is captured even if the
    snippet raises an exception or is interrupted. The callback is
    guaranteed to execute before any exceptions are re-raised.

    Args:
        source (str): The Python source code to be executed.
        callback (callable): A function to handle the trace data.

    Returns:
        list: A list of trace events captured during execution.
    """
    compiled = compile(source=source, filename="", mode="exec")

    module = ModuleType("traced_module")

    trace_next_loaded_module(done_callback)
    exec(compiled, module.__dict__)  # Execute code within the module's namespace


def trace_next_loaded_module(done_callback: DoneCallback):
    debug_heading("TRACE NEXT LOADED MODULE")
    Tracer(done_callback, None)


def on_trace(trace: Trace):
    debug_heading("Got trace")
    debug_pprint(trace)
    # Import only here, to avoid circular import problems
    from .interpreter import trace_to_history  # noqa: E402
    from .reporter import print_history  # noqa: E402

    history = trace_to_history(trace)
    print_history(history)


def _get_importer_frame() -> FrameType | None:
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


if "unittest" not in sys.modules:
    debug_heading("TRACING FROM IMPORT")
    debug_stack_frame()
    # We want to only trace the module that imports us
    # Luckily, when run as a tool with -m no importer frame gets found
    importer_frame = _get_importer_frame()
    if importer_frame:
        # When running in thonny we need to step up one level because
        # we get imported from a backend custom_import.
        # We got this extra step even when not in thonny, there is no negative impact.
        if importer_frame.f_back:
            importer_frame = importer_frame.f_back
        debug_heading("ATTACH TO FRAME")
        debug_frame(importer_frame)
        Tracer(on_trace, importer_frame)
