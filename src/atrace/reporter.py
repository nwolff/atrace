import gettext
from typing import Any, TypeAlias

from tabulate import tabulate

from .analyzer import UNASSIGN, History, Var

t = gettext.translation("atrace", "./locale", fallback=True)
_ = t.gettext


LINE, OUTPUT = _("line"), _("output")

Row: TypeAlias = dict[str, Any | None]


def variable_to_column_name(var: Var) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def history_to_table(history: History) -> list[Row]:
    all_variables = []
    has_output = False

    # Collect all variables in order of appearance.
    # Also determine if we need an output column in the table.
    for _, assignments, output in history:
        for variable in assignments or []:
            if variable not in all_variables:
                all_variables.append(variable)
        if output:
            has_output = True

    # Time to build the table datastructure
    table = []
    for loc, assignments, output in history:
        row: Row = {}
        table.append(row)

        row[LINE] = loc.line_no

        content: Any | None
        for variable in all_variables:
            if variable in assignments:
                value = assignments[variable]
                match value:
                    case None:
                        content = "None"
                    case _ if value is UNASSIGN:
                        content = None
                    case _:
                        content = value
            else:
                content = None
            row[variable_to_column_name(variable)] = content

        if has_output:
            row[OUTPUT] = output

    return table


def history_to_report(history: History) -> str:
    table = history_to_table(history)
    return tabulate(table, headers="keys", tablefmt="simple_outline")
