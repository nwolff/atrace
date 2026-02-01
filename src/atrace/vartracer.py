import copy
import inspect
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
    def __init__(self, trace: model.Trace, module_of_interest: ModuleType):
        self.trace = trace
        self.module_of_interest = module_of_interest
        self.last_locals: dict[str, Any] = {}

    def trace_vars(self, frame: FrameType, event: str, arg: Any):
        print("VT")
        if inspect.getmodule(frame) != self.module_of_interest:
            return
        if event == "return":
            self.trace.append(
                model.TraceItem(
                    line_no=frame.f_lineno,
                    function_name=frame.f_code.co_name,
                    event=model.ReturnEvent(
                        function_name=frame.f_code.co_name, return_value=arg  # XXX
                    ),
                )
            )

        code = frame.f_code

        if code.co_name not in self.last_locals:
            old_locals = {}
        else:
            old_locals = self.last_locals[code.co_name]

        locals_now = copy_carefully(filtered_variables(frame.f_locals))

        for var, new_val in filtered_variables(locals_now).items():
            if var not in old_locals or old_locals[var] != new_val:
                self.trace.append(
                    model.TraceItem(
                        line_no=frame.f_lineno,
                        function_name=frame.f_code.co_name,
                        event=model.VariableChangeEvent(
                            variable=model.Variable(scope=code.co_name, name=var),
                            value=new_val,
                        ),
                    )
                )

        self.last_locals[code.co_name] = locals_now
        return self.trace_vars
