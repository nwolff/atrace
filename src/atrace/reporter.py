import configparser
import gettext
import os
import pathlib
from typing import Any, TypeAlias

from rich import box
from rich.console import Console
from rich.table import Table

from .core.analyzer import UNASSIGN, History, Var

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

HeaderData: TypeAlias = list[str]
RowData: TypeAlias = list[str | None]
TableData: TypeAlias = tuple[HeaderData, list[RowData]]


def variable_to_column_name(var: Var) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def history_to_table_data(history: History) -> TableData:
    all_variables = []
    history_has_output = False

    # Prepare:
    # - Collect all variables in order of appearance.
    # - Determine if we need an output column in the table.
    for _, assignments, output in history:
        for variable in assignments or []:
            if variable not in all_variables:
                all_variables.append(variable)
        if output:
            history_has_output = True

    # Build headers
    headers = [LINE]
    for variable in all_variables:
        headers.append(variable_to_column_name(variable))
    if history_has_output:
        headers.append(OUTPUT)

    # Build rows
    rows = []
    for loc, assignments, output in history:
        row: RowData = []
        rows.append(row)

        row.append(str(loc.line_no))

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
                        content = str(value)
            else:
                content = None
            row.append(content)

        if history_has_output:
            row.append(output.strip() if output else None)

    return headers, rows


def table_data_to_table(table_data: TableData) -> Table:
    table = Table(box=box.ROUNDED, padding=(0, 1, 0, 2))
    headers, rows = table_data
    for header in headers:
        table.add_column(header, justify="right")
    for row in rows:
        table.add_row(*row)
    return table


def history_to_table(history: History) -> Table:
    table_data = history_to_table_data(history)
    return table_data_to_table(table_data)


def history_to_report(history: History) -> str:
    table = history_to_table(history)
    console = Console(color_system=None)
    with console.capture() as capture:
        console.print(table)
    return capture.get()
