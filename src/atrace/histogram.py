"""
Displays a view of a given program, with :
 - The code on the left
 - A histogram of how many times each line was executed on the right
"""

import argparse
import math
from collections import Counter
from typing import TypeAlias

from rich import box
from rich.console import RenderableType
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

from atrace.interpreter import Call, History, Line

from . import Trace, trace_code
from .code import (
    CODE_VIEW_WIDTH,
    add_line_numbers,
    generate_code_display,
)
from .interpreter import trace_to_history
from .tool_support import (
    Context,
    terminal_or_svg,
    visible_program_lines,
)

BAR_COLOR = "rgb(0,0,255)"

ExecutionsPerLine: TypeAlias = dict[int, int]


def filter_events(history: History) -> History:
    """Keep only events that are interesting for the histogram."""
    result: History = []
    for lineno, item in history:
        match item:
            case Call(_, _) | Line():
                result.append((lineno, item))
            case _:
                pass
    return result


def line_histogram(history: History) -> ExecutionsPerLine:
    return Counter(lineno for lineno, _ in history)


def generate_histogram_display(context: Context) -> Table:
    numbered_lines, history, current_lineno = context
    executions_per_line = line_histogram(history)
    max_hits = max(executions_per_line.values()) if executions_per_line else 1

    table = Table(show_header=False, box=None, padding=(0, 1, 0, 0))

    table.add_column(
        "Hits",
        width=int(math.log10(max(1, max_hits))) + 2,
        justify="right",
        no_wrap=True,
    )
    table.add_column("Bar", width=30, no_wrap=True)

    for lineno, line in visible_program_lines(numbered_lines, current_lineno):
        hits = executions_per_line.get(lineno, 0)

        # Calculate width relative 30-unit max
        bar_width = int((hits / max_hits) * 30) if max_hits > 0 else 0

        # Create a text object: [Hit Count] + [Space styled with background]
        bar_display = Text()
        if bar_width:
            bar_display.append(" " * bar_width, style=f"on {BAR_COLOR}")

        table.add_row(str(hits), bar_display)

    return table


def generate_code_and_histogram_display(context: Context) -> RenderableType:
    grid = Table(
        show_header=False,
        show_edge=False,
        box=box.MINIMAL,
        padding=(0, 0),
        collapse_padding=True,
        border_style="dim",
    )

    grid.add_column(width=CODE_VIEW_WIDTH, no_wrap=True)
    grid.add_column(no_wrap=True)

    grid.add_row(
        generate_code_display(context),
        generate_histogram_display(context),
    )

    # Pad so that there are empty lines at the top and bottom
    # If we'd added passing to the table above, the separation line gets too long
    return Padding(grid, (1, 0))


def run():
    parser = argparse.ArgumentParser(
        description="Displays the line histogram of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    parser.add_argument(
        "--svg",
        help="The path to save the histogram as an SVG file instead of displaying it",
    )
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        numbered_lines = add_line_numbers(source)
        history = filter_events(trace_to_history(trace))
        display = generate_code_and_histogram_display(Context(numbered_lines, history))
        with terminal_or_svg(options.svg) as console:
            console.print(display)

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
