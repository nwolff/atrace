import copy
import inspect
import sys
from types import FrameType, ModuleType
from typing import Any, TextIO

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
        except:
            v_copy = v
        res[k] = v_copy
    return res


class VarTracer:
    def __init__(self, trace: model.Trace, module_of_interest: ModuleType):
        self.trace = trace
        self.module_of_interest = module_of_interest
        self.last_locals = {}

    def trace_vars(self, frame: FrameType, event: str, arg: Any):
        if inspect.getmodule(frame) != self.module_of_interest:
            return
        if event == "return":
            return
        # print("####", event, frame.f_lineno, frame.f_code)

        code = frame.f_code

        if code.co_name not in self.last_locals:
            old_locals = {}
        else:
            old_locals = self.last_locals[code.co_name]

        locals_now = copy_carefully(filtered_variables(frame.f_locals))
        # print("locals_now", locals_now)

        for var, new_val in filtered_variables(locals_now).items():
            if var not in old_locals or old_locals[var] != new_val:
                # print("çççç", frame.f_lineno, var)
                self.trace.append(
                    model.TraceItem(
                        line_no=frame.f_lineno,
                        function_name=frame.f_code.co_name,
                        event=model.VariableChangeEvent(
                            variable=model.Variable(
                                function_name=code.co_name, name=var
                            ),
                            value=new_val,
                        ),
                    )
                )

        self.last_locals[code.co_name] = locals_now
        return self.trace_vars


class OutputLogger(object):
    """
    OutputLogger captures and logs the output produced by print statements during code execution.
    """

    def __init__(self, trace: model.Trace, stdout: TextIO):
        self.trace = trace
        self.stdout = stdout

    def write(self, text: str) -> None:
        """
        Write to stdout and record it in the trace
        """
        self.stdout.write(text)

        frame = sys._getframe(1)
        # An alternative that uses a public API, but then the type checker bothers me
        # frame = inspect.currentframe().f_back

        self.trace.append(
            model.TraceItem(
                line_no=frame.f_lineno,
                function_name=frame.f_code.co_name,
                event=model.PrintEvent(text),
            )
        )

    def flush(self):
        self.stdout.flush()
