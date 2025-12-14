import inspect
import sys
from types import FrameType
from typing import Optional

from .analyzer import trace_to_history
from .reporter import history_to_table
from .tracer import DoneCallback, Trace, Tracer


def get_importer_frame() -> Optional[FrameType]:
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


def trace_next_loaded_module(done_callback: DoneCallback):
    Tracer(done_callback, None)


def dump_report(trace: Trace):
    history = trace_to_history(trace)
    formatted_table = history_to_table(history)
    print(formatted_table)


if "unittest" not in sys.modules:
    # We want to only trace the module that imports us
    importer_frame = get_importer_frame()
    if importer_frame:
        Tracer(dump_report, importer_frame)
