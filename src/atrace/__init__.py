import atexit
import inspect
import signal
import sys
from types import FrameType
from typing import Optional, TextIO

from . import model, outputlogger, reporter, vartracer

trace: model.Trace | None = None


global_original_stdout: TextIO | None = None


global_importer_frame: FrameType | None = None


def exit_handler():
    teardown_vartrace()
    teardown_outputlogging()
    if "unittest" not in sys.modules:
        reporter.dump_report(trace)


# https://stackoverflow.com/questions/23468042/the-invocation-of-signal-handler-and-atexit-handler-in-python
def sig_handler(_signo, _frame):
    sys.exit(0)


def get_importer_frame() -> Optional[FrameType]:
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


def setup_vartrace():
    """See https://docs.python.org/3/library/sys.html#sys.settrace"""

    # We want to only trace the module that imports us
    importer_frame = get_importer_frame()
    if importer_frame:
        var_tracer = vartracer.VarTracer(trace, importer_frame)

        # Setup tracing inside of functions.
        # Order is important. This must be called before seting the trace function for the current frame
        sys.settrace(var_tracer.trace_vars)

        # Setup tracing outside of functions
        importer_frame.f_trace = var_tracer.trace_vars

        global global_importer_frame
        global_importer_frame = importer_frame


def setup_outputlogging(trace):
    global global_original_stdout
    global_original_stdout = sys.stdout
    sys.stdout = outputlogger.OutputLogger(trace=trace, stdout=sys.stdout)


def setup_exit_handlers():
    atexit.register(exit_handler)
    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
    for sig in catchable_sigs:
        signal.signal(sig, sig_handler)


def teardown_vartrace():
    sys.settrace(None)
    if global_importer_frame is not None:
        global_importer_frame.f_trace = None


def teardown_outputlogging():
    sys.stdout = global_original_stdout


def trace_next_loaded_module():
    global trace
    trace = []
    setup_outputlogging(trace)
    var_tracer = vartracer.VarTracer(trace, None)

    sys.settrace(var_tracer.trace_vars)


if "unittest" not in sys.modules:
    trace = []
    setup_vartrace()
    setup_outputlogging(trace)
    setup_exit_handlers()
