import copy
import sys
from types import FrameType, ModuleType
from typing import Any

from atrace import model


def ignore_variable(name: str, value: Any):
    return name.startswith("__") or callable(value) or isinstance(value, ModuleType)


def filtered_variables(variables: dict[str, Any]) -> dict[str, Any]:
    return {
        name: value
        for name, value in variables.items()
        if not ignore_variable(name, value)
    }


def copy_carefully(d: dict[str, Any]):
    res = {}
    for k, v in d.items():
        try:
            v_copy = copy.deepcopy(v)
        except Exception:
            v_copy = v
        res[k] = v_copy
    return res


class VarTracer:
    def __init__(self, trace: model.Trace, attached_to_frame: FrameType | None):
        self.trace = trace
        self.attached_to_frame = attached_to_frame
        self.first_frame_of_interest: FrameType | None = None
        self.last_locals: dict[str, Any] = {}
        self.last_line = -1  # XXX

    def trace_vars(self, frame: FrameType, event: str, arg: Any):
        """
        event is either 'call', 'line', 'return', 'exception' or 'opcode'
        """
        if not self.first_frame_of_interest:
            if frame.f_code.co_name == "<module>":
                # print("found frame of interest", frame)
                self.first_frame_of_interest = frame
                self.filename = frame.f_code.co_filename
            else:
                return

        # print(self.filename, frame.f_code.co_filename)
        if frame.f_code.co_filename != self.filename:
            return
        # if frame.f_code != self.module:
        #    return

        """
        print(
            "frame lineno",
            frame.f_lineno,
            ". event",
            event,
            ". module",
            frame.f_code.co_name,
            ". locals",
            filtered_variables(frame.f_locals),
        )"""

        if event in ("line", "return"):
            code = frame.f_code

            if code.co_name not in self.last_locals:
                old_locals = {}
            else:
                old_locals = self.last_locals[code.co_name]

            locals_now = copy_carefully(filtered_variables(frame.f_locals))

            for var, new_val in filtered_variables(locals_now).items():
                # print("ZZ", var, new_val)  # XXX
                if var not in old_locals or old_locals[var] != new_val:
                    self.trace.append(
                        model.TraceItem(
                            line_no=self.last_line,
                            function_name=frame.f_code.co_name,
                            event=model.VariableChangeEvent(
                                variable=model.Variable(scope=code.co_name, name=var),
                                value=new_val,
                            ),
                        )
                    )
            self.last_locals[code.co_name] = locals_now
        if event == "return":
            if frame == self.first_frame_of_interest:
                self.unload()
                # print("ITS THE END OF THE WORLD")  # XXX
            """
            self.trace.append(
                model.TraceItem(
                    line_no=frame.f_lineno,
                    function_name=frame.f_code.co_name,
                    event=model.ReturnEvent(
                        function_name=frame.f_code.co_name, return_value=arg  # XXX
                    ),
                )
            )"""
        self.last_line = frame.f_lineno
        return self.trace_vars  # Not really sure this does anything

    def unload(self):
        # print("unloading")  # XXX
        sys.settrace(None)
        if self.attached_to_frame:
            self.attached_to_frame.f_trace = None
