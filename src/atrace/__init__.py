import atexit
import inspect
import sys
from types import FrameType
from typing import Any, Optional

from . import tracers


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


def exit_handler():
    sys.stdout = original_stdout
    print(outputLogger.captured)


original_stdout = sys.stdout
outputLogger = tracers.OutputLogger(sys.stdout)


def setup():
    sys.settrace(just_kicking_off)
    # This kicks off the tracing machinery (so that the lines below work)

    # This reaches into the importing module's frame to setup tracing of code outside of functions
    importer_frame = get_importer_frame()
    if importer_frame:
        importer_frame.f_trace = tracers.trace_vars
        tracers.module_of_interest = inspect.getmodule(
            importer_frame
        )  # XXX This is dirty

        # This will work next time we enter a function.
        sys.settrace(tracers.trace_vars)
    else:
        print("Cannot trace")

    sys.stdout = outputLogger

    atexit.register(exit_handler)


setup()
