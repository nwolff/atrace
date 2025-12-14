import gettext
from typing import Any

from tabulate import tabulate

from .analyzer import History, Var

t = gettext.translation("atrace", "./locale", fallback=True)
_ = t.gettext


LINE, OUTPUT = _("line"), _("output")


def variable_to_column_name(var: Var) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def history_to_table(history: History) -> str:
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

    table = []
    for loc, assignments, output in history:
        row: dict[str, Any] = {}
        table.append(row)

        row[LINE] = loc.line_no
        for variable in all_variables:
            cell_for_variable = assignments.get(variable, "") if assignments else ""
            row[variable_to_column_name(variable)] = cell_for_variable
        if has_output:
            row[OUTPUT] = output

    return tabulate(table, headers="keys", tablefmt="simple_outline")
