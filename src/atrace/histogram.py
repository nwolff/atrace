import argparse
import math
from collections import defaultdict
from typing import TypeAlias

from rich.bar import Bar
from rich.console import Console
from rich.padding import Padding
from rich.table import Table

from . import Filters, History, Loc, Trace, trace_code, trace_to_history
from .code import (
    CODE_VIEW_WIDTH,
    NumberedLines,
    add_line_numbers,
    generate_code_display,
)
from .tool_support import visible_lines

BAR_COLOR = "rgb(0, 0, 255)"

ExecutionsPerLine: TypeAlias = dict[int, int]


def line_histogram(history: History) -> ExecutionsPerLine:
    result: ExecutionsPerLine = defaultdict(int)
    for loc, _, _ in history:
        result[loc.line_no] += 1
    return result


def generate_histogram_display(
    numbered_lines: NumberedLines, history: History, current_loc: Loc | None = None
) -> Table:
    executions_per_line = line_histogram(history)
    max_executions = max(executions_per_line.values()) if executions_per_line else 1

    table = Table(show_header=False, box=None)
    table.add_column("Hits", width=int(math.log10(max_executions)) + 2, justify="right")
    table.add_column("Bar", width=30)

    for line_number, line in visible_lines(numbered_lines, current_loc):
        num_executions = executions_per_line.get(line_number, 0)
        line_bar = Bar(
            begin=0,
            end=num_executions,
            size=max(30, max_executions),
            color=BAR_COLOR,
        )

        table.add_row(str(num_executions), line_bar)

    return table


def generate_code_and_histogram_display(
    numbered_lines: NumberedLines, history: History, current_loc: Loc | None = None
):
    grid = Table.grid(padding=(0, 0))
    grid.add_column(
        width=CODE_VIEW_WIDTH,
    )
    grid.add_column()

    grid.add_row(
        generate_code_display(numbered_lines, history, current_loc),
        generate_histogram_display(numbered_lines, history, current_loc),
    )
    # (top, right, bottom, left)
    padded_grid = Padding(grid, (1, 0, 1, 0))

    return padded_grid


def run():
    parser = argparse.ArgumentParser(
        description="Displays the line histogram of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace, filters=Filters.NONE)
        numbered_lines = add_line_numbers(source)
        console = Console()
        console.print(generate_code_and_histogram_display(numbered_lines, history))

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
