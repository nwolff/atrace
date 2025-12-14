import copy
import inspect
import sys
from types import FrameType
from typing import Any, Optional

module_of_interest = None
last_locals = {}


def ignore_variable(name: str, value: Any):
    return callable(value)  # Functions, modules, tout ça


def copy_carefully(d: dict[str, Any]):
    res = {}
    for k, v in d.items():
        if not ignore_variable(k, v):
            try:
                v_copy = copy.deepcopy(v)
            except:
                v_copy = v
            res[k] = v_copy
    return res


def trace_vars(frame: FrameType, event: str, arg: Any):
    if inspect.getmodule(frame) != module_of_interest:
        return
    if event != "line":
        return trace_vars
    code = frame.f_code
    lineno = frame.f_lineno
    locals_now = copy_carefully(frame.f_locals)
    global last_locals

    if last_locals is None:  # We're being unloaded, it's the end of the program
        return None

    if code.co_name not in last_locals:
        last_locals[code.co_name] = locals_now
        return trace_vars

    old_locals = last_locals[code.co_name]

    for var, new_val in locals_now.items():
        if not ignore_variable(var, new_val):
            if var not in old_locals:
                print(f"[{lineno}] NEW {var} = {new_val}")
            elif old_locals[var] != new_val:
                print(f"[{lineno}] MODIFIED {var}: {old_locals[var]} → {new_val}")

    for var, old_val in old_locals.items():
        if var not in locals_now:
            if not ignore_variable(var, old_val):
                print(f"[{lineno}] DELETED {var}")

    last_locals[code.co_name] = locals_now
    return trace_vars


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


# This kicks off the tracing machinery (so that the lines below work)
sys.settrace(just_kicking_off)


# This reaches into the importing module's frame to setup tracing of code outside of functions
importer_frame = get_importer_frame()
if importer_frame:
    importer_frame.f_trace = trace_vars
    module_of_interest = inspect.getmodule(importer_frame)
    # This will work next time we enter a function.
    sys.settrace(trace_vars)
else:
    print("Cannot trace")
