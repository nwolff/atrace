import inspect
import sys
from types import FrameType

from .core.analyzer import trace_to_history
from .core.tracer import DoneCallback, Trace, Tracer

from .reporter import history_to_report

try:
    from ._version import __version__  # noqa
except ImportError:
    # Fallback for local development if _version.py hasn't been generated yet
    __version__ = "0.0.0.dev0"


def get_importer_frame() -> FrameType | None:
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
    report = history_to_report(history)
    print()
    print(report)


if "unittest" not in sys.modules:
    # We want to only trace the module that imports us
    importer_frame = get_importer_frame()
    # Luckily, when run as a tool with -m no importer frame gets found
    if importer_frame:
        # When running in thonny we need to step up one level because
        # we get imported from a backend custom_import.
        # We got this extra step even when not in thonny, there is no negative impact.
        if importer_frame.f_back:
            importer_frame = importer_frame.f_back
        Tracer(dump_report, importer_frame)
