import copy
import inspect
import os
import sys
from collections.abc import Callable, Generator
from dataclasses import dataclass
from itertools import groupby
from pprint import pprint
from types import FrameType, ModuleType, TracebackType
from typing import Any, NamedTuple, TextIO, TypeAlias

"""
Everything regarding:
- The tracing itself
- The interpretation of the trace (generating a History)
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


def debug_frame(frame):
    """Log a scrubbed frame dump to stderr if DEBUG is enabled."""
    if not DEBUG:
        return

    attrs = ("f_back", "f_code", "f_lasti", "f_lineno", "f_trace", "f_trace_lines")
    frame_info = {a: getattr(frame, a) for a in attrs if hasattr(frame, a)}

    debug(f"<frame at {id(frame):#x}>: ")
    pprint(frame_info, stream=sys.stderr)


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

        prev_lineno, prev_event = self.trace[-1]
        if prev_lineno == lineno and isinstance(prev_event, TOutput):
            self.trace[-1] = lineno, TOutput(prev_event.text + text)
            return
        self.trace.append((lineno, TOutput(text)))

    def flush(self):
        self.stdout.flush()


BOUNDARY_CONAMES = ("<module>", "<string>")


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
        if self.filename_of_interest is None:
            debug_heading("LOOKING FOR START")
            debug_frame(frame)
            if frame.f_code.co_name in BOUNDARY_CONAMES:
                # We were lurking until now, finding out when to start collecting info.
                # It's time to get to work.
                self.filename_of_interest = frame.f_code.co_filename
                debug_heading("START")
                debug(f"because co_name {frame.f_code.co_name} in {BOUNDARY_CONAMES}")
                debug(f"filename of interest: {self.filename_of_interest}")
                debug(f"event: {event}")
                debug_frame(frame)

                sys.stdout = OutputLogger(trace=self.trace, stdout=self.original_stdout)
            else:
                return None

        # We don't want to step out of the file we are tracing
        if frame.f_code.co_filename != self.filename_of_interest:
            debug_heading("ignoring")
            debug(
                f"because file {frame.f_code.co_filename} != "
                f"f{self.filename_of_interest}",
            )
            debug(f"event: {event}")
            debug_frame(frame)  # This used to break thonny
            return None

        # Some very dynamic environment (such as Thonny) start loading proxies
        # and stuff during our module execution. Don't trace those.
        if ignore_function(frame.f_code.co_name):
            debug_heading("ignoring")
            debug(f"because of function name: {frame.f_code.co_name}")
            debug(f"event: {event}")
            debug_frame(frame)
            return None

        # Don't show atrace internals
        """"
        if frame.f_back and frame.f_back.f_code.co_filename == __file__:
            debug_heading("ignoring")
            debug("because frame.f_back is atrace.__init__:")
            debug(f"event: {event}")
            dump_frame(frame)
            return None

        debug_heading("tracing")
        debug(f"event: {event}")
        dump_frame(frame)
        """

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

        # Detect if we are leaving the module we wanted to trace.
        # XXX: Should unload even if we never found the filename_of_interest,
        # maybe the stragegy is simply counting calls and returns ?
        if (
            event == "return"
            and frame.f_code.co_name in BOUNDARY_CONAMES
            and frame.f_code.co_filename == self.filename_of_interest
        ):  # Unload if the job is done.
            debug_heading("Unloading")
            debug(
                "because: event is return",
                f"and co_name {frame.f_code.co_name} in {BOUNDARY_CONAMES}",
                f"and filename matches {self.filename_of_interest}",
            )

            debug_frame(frame)
            self.unload()
            return None

        return self.trace_vars

    def unload(self):
        sys.settrace(None)
        if self.attached_to_frame:
            self.attached_to_frame.f_trace = None
        sys.stdout = self.original_stdout
        self.done_callback(self.trace)


###############################################################################
# INTERPRETING THE TRACE
###############################################################################
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
    Tracer(done_callback, None)


def _get_importer_frame() -> FrameType | None:
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


# Set `STORE_TRACE` in the environment to store the trace instead of dumping it
STORE_TRACE = "STORE_TRACE" in os.environ

_trace = None


def on_trace(trace: Trace):
    if STORE_TRACE:
        _trace = trace
    else:
        from .reporter import print_history  # noqa: E402

        history = trace_to_history(trace)
        print_history(history)


if STORE_TRACE or "unittest" not in sys.modules:
    debug_heading("INIT")
    debug("atrace module being imported")
    debug_stack_frame()
    # We want to only trace the module that imports us
    # Luckily, when run as a tool with -m no importer frame gets found
    importer_frame = _get_importer_frame()
    if importer_frame:
        debug_heading("ATTACH TO FRAME")
        debug_frame(importer_frame)
        Tracer(on_trace, importer_frame)
