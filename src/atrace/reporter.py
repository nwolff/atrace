from dataclasses import dataclass
from typing import Any, TypeAlias

from icecream import ic
from tabulate import tabulate

from . import vartracer


@dataclass(frozen=True)
class Variable:
    scope: str
    name: str


@dataclass
class Instant:
    line_no: int
    variable_changes: dict[Variable, Any]
    output: str


Instants: TypeAlias = list[Instant]


def trace_to_instants(trace: vartracer.Trace) -> Instants:
    instants = []
    last_item = trace.pop(0)
    last_line = last_item.line_no
    for trace_item in trace:
        match trace_item.event:
            case vartracer.LineEvent(locals):
                pass
            case vartracer.CallEvent(locals):
                pass
            case vartracer.ReturnEvent(locals, _return_value):
                pass
            case vartracer.ExceptionEvent(_locals, _exception, _value, _traceback):
                pass
            case vartracer.OutputEvent(text):
                pass
    return instants


def variable_to_column_name(var: Variable) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def formatted_table_from_instants(instants: Instants) -> str:
    variables = []

    for instant in instants:
        for variable in instant.variable_changes:
            if variable not in variables:
                variables.append(variable)

    LINE_NO, OUTPUT = "ligne", "affichage"

    table = []
    for instant in instants:
        row: dict[str, Any] = {}
        table.append(row)

        row[LINE_NO] = instant.line_no
        for variable in variables:
            cell_for_variable = instant.variable_changes.get(variable, "")
            row[variable_to_column_name(variable)] = cell_for_variable
        row[OUTPUT] = instant.output

    return tabulate(table, headers="keys", tablefmt="simple_outline")


def dump_report(trace: vartracer.Trace) -> None:
    instants = trace_to_instants(trace)
    formatted_table = formatted_table_from_instants(instants)
    print(formatted_table)
