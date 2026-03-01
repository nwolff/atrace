"""
Displays the trace of a given python program.
"""

import argparse

from rich.console import Console

from . import Trace, trace_code, trace_to_history
from .reporter import history_to_table


def run():
    parser = argparse.ArgumentParser(
        description="Displays the trace table of the given program"
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace)
        console = Console()
        console.print()
        console.print(history_to_table(history))
        console.print()

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
