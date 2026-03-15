"""
Displays the animated trace of a given python program.
"""

import argparse

from rich.console import Console
from rich.table import Table

from . import Trace, trace_code, trace_to_history
from .code import CODE_VIEW_WIDTH, generate_code_display
from .reporter import (
    history_to_table_data,
    table_data_to_table,
)
from .tool_support import Context, add_line_numbers, animate


def max_visible_rows():
    return Console().size.height - 7  # Reserve space for headers/borders


def generate_code_and_trace_display(context: Context) -> Table:
    grid = Table.grid(padding=(1, 0))
    grid.add_column(width=CODE_VIEW_WIDTH)
    grid.add_column()
    grid.add_row(generate_code_display(context), generate_trace_display(context))
    return grid


def generate_trace_display(context: Context) -> Table:
    _, history, _ = context
    headers, rows = history_to_table_data(history)

    # Only display the rows we have room for, this has the effect of scrolling the rows
    rows = rows[-max_visible_rows() :]

    return table_data_to_table((headers, rows))


def run():
    parser = argparse.ArgumentParser(
        description="Displays an animated trace of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        numbered_lines = add_line_numbers(source)
        history = trace_to_history(trace)
        animate(numbered_lines, history, generate_code_and_trace_display)

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
