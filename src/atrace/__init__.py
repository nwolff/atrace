import copy
import inspect
import sys
from types import FrameType
from typing import Any

paused = True
last_locals = {}

ignored_variables = set(
    [
        "tid",
    ]
)


def ignore_variable(var: str):
    return var in ignored_variables


def copy_carefully_using_ignored_variables(d: dict[str, Any]):
    res = {}
    for k, v in d.items():
        if not ignore_variable(k):
            res[k] = copy.deepcopy(v)
    return res


def copy_carefully(d: dict[str, Any]):
    res = {}
    for k, v in d.items():
        try:
            v_copy = copy.deepcopy(v)
        except:
            v_copy = v
        res[k] = v_copy
    return res


def trace_vars(frame: FrameType, event: str, arg: Any):
    if paused:
        return
    # print(frame.f_lineno, frame.f_code.co_name, frame.f_locals, event)
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
        if not ignore_variable(var):
            if var not in old_locals:
                print(f"[{lineno}] NEW {var} = {new_val}")
            elif old_locals[var] != new_val:
                print(f"[{lineno}] MODIFIED {var}: {old_locals[var]} → {new_val}")

    for var in old_locals:
        if not ignore_variable(var):
            if var not in locals_now:
                print(f"[{lineno}] DELETED {var}")

    last_locals[code.co_name] = locals_now
    return trace_vars


def just_kicking_off(frame: FrameType, event: str, arg: Any):
    return None


def get_importer_frame():
    # Get the current call stack
    for frame_info in inspect.stack():
        # Filter out internal importlib frames and the current module's frame
        filename = frame_info.filename
        if not filename.startswith("<") and filename != __file__:
            return frame_info.frame
    return None


# This will work next time we enter a function.
# It also kicks off the tracing machinery (so that the lines below work)
sys.settrace(trace_vars)


# This reaches into the importing module's frame to setup tracing
importer_frame = get_importer_frame()
if importer_frame:
    importer_frame.f_trace = trace_vars
    paused = False
else:
    print("Cannot trace")
