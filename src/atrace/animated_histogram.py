import argparse

from . import Filters, Trace, trace_code, trace_to_history
from .histogram import generate_code_and_histogram_display
from .tool_support import add_line_numbers, animate


def run():
    parser = argparse.ArgumentParser(
        description="Displays the line histogram of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        numbered_lines = add_line_numbers(source)
        history = trace_to_history(trace, filters=Filters.NONE)
        animate(numbered_lines, history, generate_code_and_histogram_display)

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
