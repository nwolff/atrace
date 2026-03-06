"""
Displays a numbered and syntax highlighted representation of a given program
"""

import argparse

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from . import History, Trace, trace_code, trace_to_history
from .tool_support import NumberedLines, add_line_numbers, visible_lines

INTENSE_COLOR = 0, 0, 255

TAIL_SIZE = 3

CODE_VIEW_WIDTH = 86


def clamp(a, lower_bound, higher_bound):
    return max(lower_bound, min(a, higher_bound))


def color_for_intensity(intensity: float) -> str:
    intensity = clamp(intensity, 0, 1)
    color = tuple(int(comp * intensity) for comp in INTENSE_COLOR)
    return f"rgb({color[0]},{color[1]},{color[2]})"


def generate_code_display(
    numbered_lines: NumberedLines, history: History, current_lineno: int | None = None
) -> Table:

    if current_lineno:
        recent_history = history[-TAIL_SIZE:]
        num_items = len(recent_history)
        scale = 1.0 / num_items if num_items > 0 else 1.0
        trail = {
            lineno: color_for_intensity((index + 1) * scale)
            for index, (lineno, _) in enumerate(recent_history)
        }
    else:
        trail = {}

    table = Table(show_header=False, box=None)
    table.add_column("Code", width=CODE_VIEW_WIDTH)

    for lineno, line in visible_lines(numbered_lines, current_lineno):
        syntax_line = Syntax(
            line,
            "python",
            theme="ansi_light",
            word_wrap=False,
            line_numbers=True,
            start_line=lineno,
            background_color=trail.get(lineno),
            highlight_lines={lineno} if lineno == current_lineno else None,
        )

        table.add_row(syntax_line)

    return table


def run():
    parser = argparse.ArgumentParser(
        description="Displays the code of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace)
        numbered_lines = add_line_numbers(source)
        console = Console()
        console.print()  # Prints a blank line
        console.print(generate_code_display(numbered_lines, history))
        console.print()  # Prints a blank line

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
