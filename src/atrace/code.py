"""
Displays a numbered and syntax highlighted representation of a given program
"""

import argparse

from rich.syntax import Syntax
from rich.table import Table

from . import Trace, trace_code, trace_to_history
from .tool_support import (
    Context,
    add_line_numbers,
    terminal_or_svg,
    visible_program_lines,
)

INTENSE_COLOR = 0, 0, 255

TAIL_SIZE = 3

CODE_VIEW_WIDTH = 80


def clamp(a, lower_bound, higher_bound):
    return max(lower_bound, min(a, higher_bound))


def color_for_intensity(intensity: float) -> str:
    intensity = clamp(intensity, 0, 1)
    color = tuple(int(comp * intensity) for comp in INTENSE_COLOR)
    return f"rgb({color[0]},{color[1]},{color[2]})"


def generate_code_display(context: Context) -> Table:
    numbered_lines, history, current_lineno = context
    if current_lineno:
        recent_history = history[-TAIL_SIZE:]
        num_items = len(recent_history)
        scale = 1.0 / num_items if num_items > 0 else 1.0
        tail = {
            lineno: color_for_intensity((index + 1) * scale)
            for index, (lineno, _) in enumerate(recent_history)
        }
    else:
        tail = {}

    table = Table(show_header=False, box=None)
    table.add_column("Code", width=CODE_VIEW_WIDTH)

    for lineno, line in visible_program_lines(numbered_lines, current_lineno):
        syntax_line = Syntax(
            line,
            "python",
            theme="ansi_light",
            word_wrap=False,
            line_numbers=True,
            start_line=lineno,
            background_color=tail.get(lineno),
            highlight_lines={lineno} if lineno == current_lineno else None,
        )
        table.add_row(syntax_line)

    return table


def run():
    parser = argparse.ArgumentParser(
        description="Displays the code of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    parser.add_argument(
        "--svg",
        help="The path to save the code as an SVG file instead of displaying it",
    )
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace)
        numbered_lines = add_line_numbers(source)
        table = generate_code_display(Context(numbered_lines, history))
        with terminal_or_svg(options.svg) as console:
            console.print()
            console.print(table)
            console.print()

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
