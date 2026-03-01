import argparse

from rich.padding import Padding
from rich.table import Table

from . import Filters, History, Loc, Trace, trace_code, trace_to_history
from .code import CODE_VIEW_WIDTH, generate_code_display
from .reporter import history_to_table
from .tool_support import NumberedLines, add_line_numbers, animate


def generate_code_and_trace_display(
    numbered_lines: NumberedLines, history: History, current_loc: Loc | None = None
):
    grid = Table.grid(padding=(0, 0))
    grid.add_column(
        width=CODE_VIEW_WIDTH,
    )
    grid.add_column()

    grid.add_row(
        generate_code_display(numbered_lines, history, current_loc),
        generate_trace_display(numbered_lines, history, current_loc),
    )
    # (top, right, bottom, left)
    padded_grid = Padding(grid, (1, 0, 1, 0))

    return padded_grid


def generate_trace_display(
    _numbered_lines: NumberedLines, history: History, _current_loc: (Loc | None) = None
) -> Table:
    return history_to_table(history)


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
        history = trace_to_history(trace, filters=Filters.NONE)
        animate(numbered_lines, history, generate_code_and_trace_display)

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
