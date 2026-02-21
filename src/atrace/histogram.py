from collections import defaultdict
from typing import TypeAlias

from rich.bar import Bar
from rich.console import Console
from rich.padding import Padding
from rich.syntax import Syntax
from rich.table import Table

from .core.analyzer import History

ExecutionsPerLine: TypeAlias = dict[int, int]


def line_histogram(history: History) -> ExecutionsPerLine:
    result: ExecutionsPerLine = defaultdict(int)
    for loc, _, _ in history:
        result[loc.line_no] += 1
    return result


def display_code_with_bars(source: str, executions_per_line: ExecutionsPerLine) -> None:
    console = Console()

    numbered_lines = [(i + 1, line) for i, line in enumerate(source.splitlines())]
    max_executions = max(executions_per_line.values())

    # Create a table without borders for a clean look
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Code", ratio=2)
    table.add_column("Value", width=5, justify="right")  # XXX: 5
    table.add_column("Bar", width=50)

    for line_number, line in numbered_lines:
        # Create highlighted syntax for the individual line
        syntax_line = Syntax(
            line, "python", theme="monokai", word_wrap=False, line_numbers=True, start_line=line_number
        )

        num_executions = executions_per_line.get(line_number, 0)

        # Create a bar based on line length relative to the maximum number of executions
        line_bar = Bar(size=max_executions, begin=0, end=num_executions, color="green")

        table.add_row(syntax_line, Padding(str(num_executions), (0, 0, 0, 1)), line_bar)

    console.print(table)


if __name__ == "__main__":
    import argparse
    from types import ModuleType

    from . import trace_next_loaded_module, trace_to_history

    parser = argparse.ArgumentParser(
        description="Displays the line histogram of the given program."
    )
    parser.add_argument("program", help="The program you want the histogram of.")
    options = parser.parse_args()

    with open(options.program, "r") as content_file:
        source = content_file.read()


    def done_callback(trace):
        history = trace_to_history(trace, keep_no_effect=True)
        executions_per_line = line_histogram(history)
        display_code_with_bars(source, executions_per_line)


    compiled = compile(source=source, filename="", mode="exec")

    module = ModuleType("traced_module")

    trace_next_loaded_module(done_callback)
    exec(compiled, module.__dict__)  # Execute code within the module's namespace
