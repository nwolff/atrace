from dataclasses import dataclass
from typing import Any

from tabulate import tabulate

from . import model


def collect_variable_list(trace: model.Trace) -> list[model.Variable]:
    variable_list = []
    for traceItem in trace:
        match traceItem.event:
            case model.VariableChangeEvent(variable_name, _):
                if variable_name not in variable_list:
                    variable_list.append(variable_name)
    return variable_list


def coalesce_print_events(trace: model.Trace) -> model.Trace:
    last_print_item = None
    for trace_item in trace:
        match trace_item.event:
            case model.PrintEvent(text):
                if (
                    last_print_item is None
                    or trace_item.line_no != last_print_item.line_no
                ):
                    last_print_item = trace_item
                else:
                    last_print_item.event.text += text
                    trace_item.event = None  # Mark for deletion
            case _:
                last_print_item = None

    return [item for item in trace if item.event is not None]


def contains_prints(trace: model.Trace) -> bool:
    for trace_item in trace:
        match trace_item.event:
            case model.PrintEvent:
                return True
    return False


def variable_to_column_name(var: model.Variable) -> str:
    context = None if var.function_name == "<module>" else var.function_name
    return "(" + context + ") " + var.name if context else var.name


@dataclass
class Line:
    line_no: int
    variable_changes: dict[str, Any]
    output: str | None


def dump_report(trace: model.Trace) -> None:
    trace = coalesce_print_events(trace)

    # Build intermediate "lines" datastructure, that collects all events that happen on a given line
    lines = []
    current_line = None
    for trace_item in trace:
        if current_line is None or current_line.line_no != trace_item.line_no:
            current_line = Line(trace_item.line_no, {}, None)
            lines.append(current_line)

        match trace_item.event:
            case model.VariableChangeEvent(variable, value):
                # Don't clobber a new value if it changes on the same line
                # (this happens for example in tight loops)
                if variable in current_line.variable_changes:
                    current_line = Line(trace_item.line_no, {}, None)
                    lines.append(current_line)

                current_line.variable_changes[variable_to_column_name(variable)] = value
            case model.PrintEvent(text):
                current_line.output = text

    # The extra spaces so the names cannot collide with variable names
    LINE_NO, OUTPUT = " ligne", "affichage "

    variable_list = collect_variable_list(trace)
    headers = [LINE_NO] + [variable_to_column_name(v) for v in variable_list] + [OUTPUT]
    table = []
    for line in lines:
        table_row = [line.line_no]
        for column_name in headers[1:-1]:
            variable_value = line.variable_changes.get(column_name)
            if variable_value:
                table_row.append(variable_value)
            else:
                table_row.append(None)
        table_row.append(line.output)
        table.append(table_row)

    print(tabulate(table, headers=headers, tablefmt="outline"))
