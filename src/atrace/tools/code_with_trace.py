import argparse
from types import ModuleType

from rich.console import Console
from rich.layout import Layout
from rich.syntax import Syntax

from atrace import trace_next_loaded_module
from atrace.core.analyzer import Filters, History, trace_to_history
from atrace.reporter import history_to_table


def display_code_with_trace(source: str, history: History):
    trace_table = history_to_table(history)

    console = Console()
    layout = Layout()
    code_layout = Layout(
        Syntax(
            source,
            "python",
            theme="monokai",
            word_wrap=False,
            line_numbers=True,
        ),
        name="code",
    )
    trace_layout = Layout(trace_table)
    layout.split_row(code_layout, trace_layout)
    console.print(layout)


def run():
    parser = argparse.ArgumentParser(
        description="Displays the trace table of the given program"
    )
    parser.add_argument("program", help="The program you want the trace of.")
    options = parser.parse_args()

    with open(options.program, "r") as content_file:
        source = content_file.read()
    compiled = compile(source, "", "exec")
    module = ModuleType("traced_module")

    def done_callback(trace):
        history = trace_to_history(trace, filters=Filters.NONE)
        display_code_with_trace(source, history)

    trace_next_loaded_module(done_callback)
    exec(compiled, module.__dict__)  # Execute code within the module's namespace
