import copy
import inspect
import sys
from dataclasses import dataclass
from types import FrameType
from typing import Any

from atrace import model

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


class OutputLogger(object):
    """
    OutputLogger captures and logs the output produced by print statements during code execution.
    """

    def __init__(self, stdout):
        self.stdout = stdout
        self.captured = []

    def write(self, text: str) -> None:
        """
        Log the provided text along with the current line number.
        """
        self.stdout.write(text)

        frame = sys._getframe(1)
        line_number = frame.f_lineno
        self.captured.append(model.PrintEvent(line_number, text))

    def flush(self):
        self.stdout.flush()
