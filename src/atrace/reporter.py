import configparser
import gettext
import os
import pathlib
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, TypeAlias

from rich import box, get_console
from rich.table import Table

from . import (
    UNASSIGN,
    Assignments,
    Call,
    History,
    LineEffects,
    Raise,
    Return,
    Var,
)

"""
Takes an execution history and builds an execution table, displaying for each line:
 - Variable assignments
 - The eventual output
"""

# When running in thonny:
# - Use 120 columns for the table (Thonny's shell always reports 80)
# - Extract the language from the thonny config (because Thonny doesn't pass the
# language as an # environment variable)
with suppress(OSError, configparser.Error):
    thonny_dir = os.environ.get("THONNY_USER_DIR")
    if thonny_dir:  # We're in thonny
        os.environ["COLUMNS"] = "120"

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


def format_value(value: Any) -> str:
    match value:
        case None:
            return "None"
        case _ if value is UNASSIGN:
            return ""
        case _:
            return _human_double_quote(value)


def format_output(output: str | None) -> str:
    return output.strip() if output else ""


def format_exception(e: BaseException | None) -> str:
    return repr(e) if e else ""


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


def _remove_functions(assignments: Assignments) -> Assignments:
    """Remove variables that contain functions in the given assignments."""
    return {var: val for var, val in assignments.items() if not callable(val)}


def _filter_functions_in_assignments(history: History) -> History:
    """Remove variables that contain functions from assignments and calls.

    If after filtering there are no effects left, remove that LineEffects entirely.
    """
    result: History = []
    for lineno, item in history:
        match item:
            case Call(function_name, bindings):
                result.append(
                    (lineno, Call(function_name, _remove_functions(bindings)))
                )
            case LineEffects(assignments, output):
                assignments = _remove_functions(assignments)
                if assignments or output is not None:
                    result.append((lineno, LineEffects(assignments, output)))
            case _:
                result.append((lineno, item))
    return result


@dataclass(frozen=True)
class LeftAligned:
    header: str


HeaderData: TypeAlias = str | LeftAligned
RowData: TypeAlias = list[str | None]
TableData: TypeAlias = tuple[list[HeaderData], list[RowData]]

VarOrFunction: TypeAlias = Var | str


def _prepare(history: History) -> tuple[list[Var | str], bool, bool]:
    """
    # - Collect all variables and functions, in order of appearance in the trace.
    # - Determine if we need an exception column in the table.
    # - Determine if we need an output column in the table.
    """
    cols_dict: dict[VarOrFunction, None] = {}

    def add_to_cols(*items):
        for item in items:
            cols_dict[item] = None

    history_has_output = False
    history_has_exception = False
    for _, item in history:
        match item:
            case Call(function_name, bindings):
                add_to_cols(function_name, *bindings)
            case LineEffects(assignments, output):
                add_to_cols(*assignments)
                if output is not None:
                    history_has_output = True
            case Raise(_, _, _):
                history_has_exception = True

    return list(cols_dict), history_has_exception, history_has_output


def header_data(var_or_func: VarOrFunction) -> HeaderData:
    match var_or_func:
        case Var(scope, name):
            return name if scope == "<module>" else f"({scope}) {name}"
        case str():
            return LeftAligned(var_or_func)


ITS_A_CALL = object()


def history_to_table_data(history: History) -> TableData:
    """Build an intermediate representation of the trace table.

    All the headers and rows are complete.
    """
    history = _filter_functions_in_assignments(history)

    all_vars_or_funcs, history_has_exception, history_has_output = _prepare(history)

    # Build table columns
    headers: list[HeaderData] = [LINE]
    for var_or_func in all_vars_or_funcs:
        headers.append(header_data(var_or_func))
    if history_has_output:
        headers.append(OUTPUT)
    if history_has_exception:
        headers.append(EXCEPTION)

    call_stack: list[str] = []

    def recursive_depth(function_name) -> int:
        return call_stack.count(function_name) if call_stack else 0

    # Build rows
    rows = []
    for lineno, history_item in history:
        assignments: Assignments = {}
        output: str | None = None
        exception: Exception | None = None
        function_name: str | None = None
        return_value: Any | None = ITS_A_CALL

        # All these cases are capturing variables that we use just below,
        # they are doing something, despite the `pass`
        match history_item:
            case Call(function_name, assignments):
                call_stack.append(function_name)
            case LineEffects(assignments, output):
                pass
            case Raise(_, exception, _):
                pass
            case Return(return_value):
                function_name = call_stack.pop()

        row: RowData = [str(lineno)]

        for var_or_func in all_vars_or_funcs:
            content = ""
            match var_or_func:
                case Var(_, _) as var if var in assignments:
                    content = format_value(assignments[var])
                case str():
                    content = "│  " * recursive_depth(var_or_func)
                    if function_name == var_or_func:
                        if return_value == ITS_A_CALL:
                            content = "│  " * (recursive_depth(var_or_func) - 1)
                            content += f"{function_name}("
                            content += ",".join(
                                format_value(v) for v in assignments.values()
                            )
                            content += ")"
                        else:
                            content += "└─ "
                            if return_value is not None:
                                content += format_value(return_value)
            row.append(content)

        if history_has_output:
            row.append(format_output(output))
        if history_has_exception:
            row.append(format_exception(exception))

        if assignments or output or exception or function_name:
            rows.append(row)

    return headers, rows


def table_data_to_table(table_data: TableData) -> Table:
    """Generate a rich Table from the given TableData."""

    # padding goes (top, right, bottom, left)
    table = Table(box=box.ROUNDED, padding=(0, 1, 0, 1), header_style="none")

    headers, rows = table_data

    for header in headers:
        match header:
            case LeftAligned(header):
                table.add_column(header, justify="left")
            case _:
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
    get_console().print(table)
