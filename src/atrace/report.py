from dataclasses import dataclass
from typing import Any, TypeAlias

from tabulate import tabulate

from . import model


@dataclass
class Instant:
    line_no: int
    variable_changes: dict[model.Variable, Any]
    output: str


Instants: TypeAlias = list[Instant]


def trace_to_instants(trace: model.Trace) -> Instants:
    instants = []
    instant = None
    for trace_item in trace:
        if instant is None or instant.line_no != trace_item.line_no:
            instant = Instant(trace_item.line_no, {}, "")
            instants.append(instant)

        match trace_item.event:
            case model.PrintEvent(text):
                instant.output += text
            case model.VariableChangeEvent(variable, value):
                # Don't clobber an existing value a variable if it changes again on the same line
                # (this happens for example in tight loops)
                if variable in instant.variable_changes:
                    instant = Instant(trace_item.line_no, {}, "")
                    instants.append(instant)
                instant.variable_changes[variable] = value
            case model.ReturnEvent():
                pass  # XXX

    return instants


def variable_to_column_name(var: model.Variable) -> str:
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


def dump_report(trace: model.Trace) -> None:
    instants = trace_to_instants(trace)
    formatted_table = formatted_table_from_instants(instants)
    print(formatted_table)
