import configparser
import gettext
import os
import pathlib
import re
from contextlib import suppress
from typing import Any, TypeAlias

from rich import box
from rich.console import Console
from rich.table import Table

from . import UNASSIGN, Assignments, History, Var

# Make localization work in thonny:
# Thonny does not pass environment variables to the running program,
# so we dig out the UI language from Thonny's configuration file.
with suppress(OSError, configparser.Error):
    if not os.getenv("LANG"):
        thonny_dir = os.environ.get("THONNY_USER_DIR")
        if thonny_dir:
            config_path = os.path.join(thonny_dir, "configuration.ini")
            config = configparser.ConfigParser()
            config.read(config_path)
            language = config.get("general", "language", fallback=None)
            if language:
                os.environ["LANG"] = language

LOCALE_DIR = pathlib.Path(__file__).parent / "locale"

t = gettext.translation("atrace", str(LOCALE_DIR), fallback=True)
_ = t.gettext

LINE, OUTPUT = _("line"), _("output")

HeaderData: TypeAlias = list[str]
RowData: TypeAlias = list[str | None]
TableData: TypeAlias = tuple[HeaderData, list[RowData]]


def format_variable(var: Var) -> str:
    return var.name if var.scope == "<module>" else f"({var.scope}) {var.name}"


def format_value(value: Any) -> str | None:
    match value:
        case None:
            return "None"
        case _ if value is UNASSIGN:
            return None
        case _:
            return _human_double_quote(value)


def format_output(output: str | None) -> str | None:
    return output.strip() if output else None


def _human_double_quote(data):
    text = repr(data)
    # Replace ' if it's at the start/end of a string
    # OR next to structural chars , [ ] ( ) { } :
    # Pattern Matches ' only if it's NOT surrounded by
    # alphanumeric characters on both sides
    pattern = r"(?<!\w)'|'(?!\w)"
    return re.sub(pattern, '"', text)


def _filter_function_assignment(history: History) -> History:
    def _remove_functions(assignments: Assignments) -> Assignments:
        """Remove variables that contain functions the given assignments."""
        return {var: val for var, val in assignments.items() if not callable(val)}

    """Remove variables that contain functions from the assignments in History."""
    return [
        (loc, _remove_functions(assignments), output)
        for loc, assignments, output in history
    ]


def _filter_no_effect(history: History) -> History:
    """Remove history items that neither assign nor output."""
    return [
        (loc, assignments, output)
        for loc, assignments, output in history
        if assignments or output
    ]


def history_to_table_data(history: History) -> TableData:
    history = _filter_function_assignment(history)
    history = _filter_no_effect(history)
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
        headers.append(format_variable(variable))
    if history_has_output:
        headers.append(OUTPUT)

    # Build rows
    rows = []
    for loc, assignments, output in history:
        row: RowData = []
        rows.append(row)

        row.append(str(loc.line_no))

        for variable in all_variables:
            if variable in assignments:
                content = format_value(assignments[variable])
            else:
                content = None
            row.append(content)

        if history_has_output:
            row.append(format_output(output))

    return headers, rows


def table_data_to_table(table_data: TableData) -> Table:
    table = Table(box=box.ROUNDED, padding=(0, 1, 0, 2), header_style="none")
    headers, rows = table_data
    for header in headers:
        table.add_column(header, justify="right")
    for row in rows:
        table.add_row(*row)
    return table


def history_to_table(history: History) -> Table:
    table_data = history_to_table_data(history)
    return table_data_to_table(table_data)


def print_history(history: History) -> None:
    table = history_to_table(history)
    console = Console()
    console.print(table)
