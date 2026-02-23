import copy
import inspect
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import IntFlag, auto
from itertools import groupby
from operator import itemgetter
from types import FrameType, ModuleType, TracebackType
from typing import Any, TextIO, TypeAlias

"""
Everything regarding:
- The tracing itself
- The interpretation of the trace
- The automatic start of tracing when one imports the module

The basic mechanism of python tracing is explained here:
    https://docs.python.org/3/library/sys.html#sys.settrace
"""

try:
    from ._version import __version__  # noqa
except ImportError:
    # Fallback for local development if _version.py hasn't been generated yet
    __version__ = "0.0.0.dev0"


"""
1. TRACING

The models and classes that collect the trace.
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
    The interpreter is about to execute a new line of code
    or re-execute the condition of a loop
    """


@dataclass(frozen=True)
class Call(ExecutionEvent):
    """
    A function is called or some other code block entered.
    This is emitted at the point of entering the function.

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
class ExceptionOccurred(ExecutionEvent):
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


Event: TypeAlias = Line | Call | Return | ExceptionOccurred | Output

Trace: TypeAlias = list[tuple[Loc, Event]]

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
        if self.filename_of_interest is None:
            if frame.f_code.co_name == CONAME:
                # We were lurking until now, finding out when to start collecting info.
                # It's time to get to work.
                self.filename_of_interest = frame.f_code.co_filename
                sys.stdout = OutputLogger(trace=self.trace, stdout=self.original_stdout)
            else:
                return None

        # We don't want to step out of the file we are tracing
        if frame.f_code.co_filename != self.filename_of_interest:
            return None

        # Some very dynamic environment (such as Thonny) start loading proxies
        # and stuff during our module execution. Don't trace those.
        if ignore_function(frame.f_code.co_name):
            return None

        globs = copy_carefully(filtered_variables(frame.f_globals))
        locs = (
            {}
            if frame.f_locals is frame.f_globals
            else copy_carefully(filtered_variables(frame.f_locals))
        )

        trace_event: Event | None = None
        match event:
            case "line":
                trace_event = Line(globals=globs, locals=locs)
            case "call":
                trace_event = Call(globals=globs, locals=locs)
            case "return":
                trace_event = Return(globals=globs, locals=locs, return_value=arg)
            case "exception":
                trace_event = ExceptionOccurred(
                    globals=globs,
                    locals=locs,
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


"""
2. Interpreting the trace

Takes a raw trace to make sense of it:
    - Detects variable assignments and the line where they occurred
    - Coalesces subsequent outputs that happen on the same line together

The result of this phase is a History
"""


@dataclass(frozen=True)
class Var:
    scope: str
    name: str


UNASSIGN = object()

Assignments: TypeAlias = dict[Var, Any]

UnpackedHistory: TypeAlias = Iterable[tuple[Loc, Assignments | str]]

HistoryItem: TypeAlias = tuple[Loc, Assignments, str | None]
History: TypeAlias = list[HistoryItem]


@dataclass
class Activation:
    locals: Symbols
    loc_awaiting_assignments: Loc | None


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

    current_globals: Symbols = {}
    activations = [Activation({}, Loc("guard", 0))]

    for loc, event in trace:
        match event:
            case Call(_, locs):
                activations.append(Activation(locs, None))
                # Capture the function bindings,
                local_assignments = diff(loc.function_name, {}, locs)
                yield loc, local_assignments

            case Line(globs, locs) | Return(globs, locs):
                activation = activations[-1]
                local_assignments = diff(loc.function_name, activation.locals, locs)
                global_assignments = diff("<module>", current_globals, globs)
                assignments = local_assignments | global_assignments

                if activation.loc_awaiting_assignments:
                    yield activation.loc_awaiting_assignments, assignments

                activation.locals = locs
                current_globals = globs
                if isinstance(event, Line):
                    activation.loc_awaiting_assignments = loc
                elif isinstance(event, Return):
                    activations.pop()

            case Output(text):
                yield loc, text


def _join_outputs(unpacked: UnpackedHistory) -> Iterable[HistoryItem]:
    """
    Coalesce consecutive events that occur on the same line: outputs, assignments
    """
    for loc, group in groupby(unpacked, key=itemgetter(0)):
        pending_output = None

        for _, item in group:
            if isinstance(item, str):
                pending_output = (pending_output or "") + item
            else:
                yield loc, item, pending_output
                pending_output = None

        if pending_output:
            yield loc, {}, pending_output


def _filter_zero_lines(history: History) -> History:
    """
    An artifact of tracing is events that happen before line 1 of the program is run
    """
    return [
        (loc, assignments, output)
        for loc, assignments, output in history
        if loc.line_no != 0
    ]


def _filter_no_effect(history: History) -> History:
    """ " Remove history items that neither assign nor output"""
    return [
        (loc, assignments, output)
        for loc, assignments, output in history
        if assignments or output
    ]


def _remove_functions(assignments: Assignments):
    return {var: val for var, val in assignments.items() if not callable(val)}


def _filter_function_assignment(history: History) -> History:
    return [
        (loc, _remove_functions(assignments), output)
        for loc, assignments, output in history
    ]


class Filters(IntFlag):
    NONE = 0
    NO_EFFECT = auto()
    FUNCTION_ASSIGNMENT = auto()


def trace_to_history(trace: Trace, filters: Filters) -> History:
    unpacked = _trace_to_unpacked_history(trace)
    joined = list(_join_outputs(unpacked))
    result = _filter_zero_lines(joined)

    if Filters.FUNCTION_ASSIGNMENT & filters:
        result = _filter_function_assignment(result)

    # This must come last (because the previous step may have turned an assignment
    # into a no effect item)
    if Filters.NO_EFFECT & filters:
        result = _filter_no_effect(result)

    return result


"""
3. The automatic tracing when one imports the module
"""

# Import after the rest of the file, to avoid circular imports
from .reporter import print_history  # noqa: E402


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


def _dump_report(trace: Trace):
    history = trace_to_history(trace, Filters.FUNCTION_ASSIGNMENT | Filters.NO_EFFECT)
    print_history(history)


if "unittest" not in sys.modules:
    # We want to only trace the module that imports us
    importer_frame = _get_importer_frame()
    # Luckily, when run as a tool with -m no importer frame gets found
    if importer_frame:
        # When running in thonny we need to step up one level because
        # we get imported from a backend custom_import.
        # We got this extra step even when not in thonny, there is no negative impact.
        if importer_frame.f_back:
            importer_frame = importer_frame.f_back
        Tracer(_dump_report, importer_frame)
