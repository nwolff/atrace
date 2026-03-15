"""
Displays the trace of a given python program.
"""

import argparse

from atrace.tool_support import terminal_or_svg

from . import Trace, trace_code, trace_to_history
from .reporter import history_to_table


def run():
    parser = argparse.ArgumentParser(
        description="Displays the trace table of the given program"
    )
    parser.add_argument("program", help="The path to a python file")
    parser.add_argument(
        "--svg",
        help="The path to save the trace as an SVG file instead of displaying it",
    )
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace)
        table = history_to_table(history)

        with terminal_or_svg(options.svg) as console:
            console.print()
            console.print(table)
            console.print()

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
