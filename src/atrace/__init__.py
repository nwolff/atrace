import atexit
import inspect
import signal
import sys
from types import FrameType
from typing import Any, Optional

from . import model, outputlogger, report, vartracer

trace: model.Trace = []


def just_kicking_off(frame: FrameType, event: str, arg: Any):
    return None


def get_importer_frame() -> Optional[FrameType]:
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


original_stdout = sys.stdout


def exit_handler():
    sys.stdout = original_stdout
    report.dump_report(trace)


# https://stackoverflow.com/questions/23468042/the-invocation-of-signal-handler-and-atexit-handler-in-python
def sig_handler(_signo, _frame):
    sys.exit(0)


def setup():
    """See https://docs.python.org/3/library/sys.html#sys.settrace for an explanation of all the convoluted things in here"""

    # This kicks off the tracing machinery (so that the lines below work)
    sys.settrace(just_kicking_off)

    # We want to only trace the module that imports us
    importer_frame = get_importer_frame()
    if importer_frame:
        module_of_interest = inspect.getmodule(importer_frame)
        if module_of_interest:
            var_tracer = vartracer.VarTracer(trace, module_of_interest)

            # Setup tracing outside of functions
            importer_frame.f_trace = var_tracer.trace_vars

            # Setup tracing inside of functions
            sys.settrace(var_tracer.trace_vars)

    sys.stdout = outputlogger.OutputLogger(trace=trace, stdout=sys.stdout)

    atexit.register(exit_handler)
    catchable_sigs = set(signal.Signals) - {signal.SIGKILL, signal.SIGSTOP}
    for sig in catchable_sigs:
        signal.signal(sig, sig_handler)


setup()
