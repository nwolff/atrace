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

from . import UNASSIGN, Assignments, Call, History, Line, Raise, Var

"""
Takes an execution history and builds an execution table, displaying for each line:
 - Variable assignments
 - The eventual output
"""

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

LINE, OUTPUT, EXCEPTION = _("line"), _("output"), _("exception")


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


def format_exception(e: BaseException | None) -> str | None:
    return repr(e) if e else None


def _human_double_quote(data):
    """Replace single quotes by double quotes.
    The goal is to represent strings like most humans do.
    It's implemented with a simple regex, and the result may not be valid python
    (one could not use it directly in code), but it's OK, our goal is cosmetic."""
    text = repr(data)
    # Replace ' if it's at the start/end of a string
    # OR next to structural chars , [ ] ( ) { } :
    # Pattern Matches ' only if it's NOT surrounded by
    # alphanumeric characters on both sides
    pattern = r"(?<!\w)'|'(?!\w)"
    return re.sub(pattern, '"', text)


def remove_functions(assignments: Assignments) -> Assignments:
    """Remove variables that contain functions in the given assignments."""
    return {var: val for var, val in assignments.items() if not callable(val)}


def _filter_functions_in_assignments(history: History) -> History:
    """Remove variables that contain functions from all assignments in History."""
    result: History = []
    for lineno, item in history:
        match item:
            case Call(function_name, bindings):
                result.append((lineno, Call(function_name, remove_functions(bindings))))
            case Line(assignments, output):
                result.append((lineno, Line(remove_functions(assignments), output)))
            case _:
                result.append((lineno, item))
    return result


def _filter_no_effect_lines(history: History) -> History:
    """Remove history lines that neither assign nor output."""
    result: History = []
    for lineno, item in history:
        match item:
            case Line(assignments, output):
                if assignments or output:
                    result.append((lineno, item))
            case _:
                result.append((lineno, item))
    return result


HeaderData: TypeAlias = list[str]
RowData: TypeAlias = list[str | None]
TableData: TypeAlias = tuple[HeaderData, list[RowData]]


def history_to_table_data(history: History) -> TableData:
    """Build an intermediate representation of the trace table where all the data
    has been generated and is properly represented as strings"""

    history = _filter_functions_in_assignments(history)
    history = _filter_no_effect_lines(history)

    # Prepare:
    # - Collect all variables in order of appearance.
    # - Determine if we need an output column in the table.
    # - Determine if we need an exception column in the table.
    raw_vars: list[Any] = []
    history_has_output = False
    history_has_exception = False
    for _, item in history:
        match item:
            case Call(_, bindings):
                raw_vars.extend(bindings)
            case Line(assignments, output):
                raw_vars.extend(assignments)
                if output:
                    history_has_output = True
            case Raise(_, _, _):
                history_has_exception = True

    # dict.fromkeys() removes duplicates and preserves the order of appearance
    all_variables = list(dict.fromkeys(raw_vars))

    # Build headers
    headers = [LINE]
    for variable in all_variables:
        headers.append(format_variable(variable))
    if history_has_output:
        headers.append(OUTPUT)
    if history_has_exception:
        headers.append(EXCEPTION)

    # Build rows
    rows = []
    for lineno, item in history:
        item_assignments = {}
        item_output = None
        item_exception = None
        match item:
            case Call(_, bindings):
                item_assignments = bindings
            case Line(assignments, output):
                item_assignments = assignments
                item_output = output
            case Raise(_, value, _):
                item_exception = value

        row: RowData = [str(lineno)]
        for variable in all_variables:
            if variable in item_assignments:
                content = format_value(item_assignments[variable])
            else:
                content = None
            row.append(content)

        if history_has_output:
            row.append(format_output(item_output))
        if history_has_exception:
            row.append(format_exception(item_exception))

        if item_assignments or item_output or item_exception:
            rows.append(row)

    return headers, rows


def table_data_to_table(table_data: TableData) -> Table:
    """Generate a rich Table from the given TableData."""

    table = Table(box=box.ROUNDED, padding=(0, 1, 0, 2), header_style="none")
    headers, rows = table_data
    for header in headers:
        table.add_column(header, justify="right")
    for row in rows:
        table.add_row(*row)
    return table


def history_to_table(history: History) -> Table:
    """The main entrypoint: generate the Table of a given History."""
    table_data = history_to_table_data(history)
    return table_data_to_table(table_data)


def print_history(history: History) -> None:
    table = history_to_table(history)
    console = Console()
    console.print(table)
