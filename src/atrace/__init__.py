import copy
import inspect
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from types import FrameType, ModuleType, TracebackType
from typing import Any, TextIO, TypeAlias

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

"""
###############################################################################
# TRACING
###############################################################################

The models and classes that collect the trace.
"""

Symbols: TypeAlias = dict[str, Any]


@dataclass(frozen=True)
class Capturing:
    globals: Symbols
    locals: Symbols


@dataclass(frozen=True)
class TLine(Capturing):
    """
    The interpreter is about to execute a new line of code
    or re-execute the condition of a loop
    """


@dataclass(frozen=True)
class TCall(Capturing):
    """
    A function is called or some other code block entered.
    This is emitted at the point of entering the function.

    One can already see:
        - The function name
        - The bound parameters
    """

    function_name: str


@dataclass(frozen=True)
class TReturn(Capturing):
    """
    A function or other code block is about to return.
    """

    return_value: Any


@dataclass(frozen=True)
class TException(Capturing):
    """
    An exception has occurred
    """

    type: type
    value: BaseException
    traceback: TracebackType


@dataclass(frozen=True)
class TOutput:
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

        previous = self.trace[-1]
        if previous:
            previous_lineno, previous_event = previous
            if previous_lineno == lineno and isinstance(previous_event, TOutput):
                self.trace[-1] = lineno, TOutput(previous_event.text + text)
                return
        self.trace.append((lineno, TOutput(text)))

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
###############################################################################
# INTERPRETING THE TRACE
###############################################################################

Takes a raw trace to make sense of it:
    - Detects variable assignments and the line where they occurred
    - Coalesces subsequent outputs that happen on the same line together

The result of this phase is a History
"""


@dataclass(frozen=True)
class Var:
    scope: str
    name: str


class Unassign:
    def __repr__(self):
        return "<UNASSIGN>"


UNASSIGN = Unassign()

Assignments: TypeAlias = dict[Var, Any]


@dataclass(frozen=True)
class Call:
    function_name: str
    bindings: Assignments


@dataclass(frozen=True)
class Return:
    return_value: Any


@dataclass(frozen=True)
class Raise:
    type: type
    value: BaseException
    traceback: TracebackType


@dataclass(frozen=True)
class Line:
    assignments: Assignments
    output: str | None


HistoryItem: TypeAlias = tuple[int, Line | Call | Return | Raise]
History: TypeAlias = list[HistoryItem]


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


@dataclass
class MutableLine:
    assignments: Assignments
    output: str | None


@dataclass(frozen=True)
class AssignmentsForLine:
    lineno: int
    assignments: Assignments


@dataclass(frozen=True)
class OutputForLine:
    lineno: int
    text: str


# An intermediate data structure in which the Assignments and Output are still separate
UnpackedHistory: TypeAlias = Iterable[
    tuple[int, MutableLine | Call | Return | Raise] | AssignmentsForLine | OutputForLine
]


@dataclass
class Activation:
    function_name: str
    locals: Symbols
    last_line_no: int


def _trace_to_unpacked_history(trace: Trace) -> UnpackedHistory:
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
                    yield AssignmentsForLine(activation.last_line_no, a)

                yield lineno, MutableLine({}, None)
                current_globals = globs
                activation.locals = locs
                activation.last_line_no = lineno

            case TReturn(globs, locs, return_value):
                activation = activations[-1]
                a = _compute_assignments(activation, globs, locs)
                if a:
                    yield AssignmentsForLine(activation.last_line_no, a)

                current_globals = globs
                yield lineno, Return(return_value)
                activations.pop()

            case TException(globs, locs, _exception, value, traceback):
                activation = activations[-1]
                a = _compute_assignments(activation, globs, locs)
                if a:
                    yield AssignmentsForLine(activation.last_line_no, a)

                current_globals = globs
                yield lineno, Raise(_exception, value, traceback)

            case TOutput(text):
                activation = activations[-1]
                yield OutputForLine(activation.last_line_no, text)


MutableHistory: TypeAlias = list[tuple[int, MutableLine | Call | Return | Raise]]


def _merge_assignments_and_outputs(unpacked: UnpackedHistory) -> MutableHistory:
    """Merge outputs and assignments into the *preceding* Line object.
    This is not a generator because we mutate things after we yield them,
    we don't want anyone to be sensitive to that."""
    history: MutableHistory = []
    target: MutableLine | None = None

    for x in unpacked:
        match x:
            case lineno, MutableLine(_, _) as ml:
                target = ml
                history.append((lineno, ml))  # type: ignore

            case AssignmentsForLine(target_lineno, assignments):
                if target:
                    target.assignments = assignments
                else:
                    target = MutableLine(assignments, None)
                    history.append((target_lineno, target))

            case OutputForLine(target_lineno, text):
                if target:
                    target.output = text
                else:
                    target = MutableLine({}, text)
                    history.append((target_lineno, target))

            case lineno, item:
                target = None
                history.append((lineno, item))

    return history


def _freeze(merged: MutableHistory) -> History:
    result: History = []
    for lineno, item in merged:
        match item:
            case MutableLine(assignments, output):
                result.append((lineno, Line(assignments, output)))

            case _:
                result.append((lineno, item))

    return result


def _filter_artifacts(history: History) -> History:
    """History contains extra implementation artifacts:
    - It always contains an extra return at the end that's not part of our program.
      We get rid of that
    - Depending on how the trace was captured it sometimes starts with a call into the
      module with lineno 0. We get rid of that as well."""

    if len(history) < 2:
        return history

    lineno, _ = history[0]
    if lineno == 0:
        return history[1:-1]
    else:
        return history[:-1]


def trace_to_history(trace: Trace) -> History:
    unpacked = _trace_to_unpacked_history(trace)
    merged = _merge_assignments_and_outputs(unpacked)
    frozen = _freeze(merged)
    return _filter_artifacts(frozen)


###############################################################################
# Running the trace
###############################################################################


def trace_code(source: str, done_callback: DoneCallback) -> None:
    """
    Given the source of a python program, returns its trace.

    We need the callback architecture because some snippets may raise exceptions
    or otherwise be interrupted. In that case:
    - The callback will first always be called
    - Any exception will be raised after that
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


# Import only here, to avoid circular import problems
from .reporter import print_history  # noqa: E402


def _dump_report(trace: Trace):
    history = trace_to_history(trace)
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
