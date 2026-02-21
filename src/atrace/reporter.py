import configparser
import gettext
import os
import pathlib
from typing import Any, TypeAlias

from tabulate import tabulate

from .analyzer import UNASSIGN, History, Var

# Make localization work in thonny:
# Thonny does not pass environment variables to the running program,
# so we dig out the UI language from Thonny's configuration file.
try:
    if not os.getenv("LANG"):
        thonny_dir = os.environ.get("THONNY_USER_DIR")
        if thonny_dir:
            config_path = os.path.join(thonny_dir, "configuration.ini")
            config = configparser.ConfigParser()
            config.read(config_path)
            language = config.get("general", "language")
            if language:
                os.environ["LANG"] = language
except Exception:
    pass

LOCALE_DIR = pathlib.Path(__file__).parent / "locale"

t = gettext.translation("atrace", str(LOCALE_DIR), fallback=True)
_ = t.gettext


LINE, OUTPUT = _("line"), _("output")

Row: TypeAlias = dict[str, Any | None]


def variable_to_column_name(var: Var) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def history_to_table(history: History) -> list[Row]:
    all_variables = []
    has_output = False

    # Prepare:
    # - Collect all variables in order of appearance.
    # - Determine if we need an output column in the table.
    for _, assignments, output in history:
        for variable in assignments or []:
            if variable not in all_variables:
                all_variables.append(variable)
        if output:
            has_output = True

    # Time to build the table
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
    return tabulate(
        table,
        headers="keys",
        stralign="right",
        disable_numparse=True,
        tablefmt="rounded_outline",
    )
