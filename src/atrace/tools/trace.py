import argparse
from types import ModuleType

from rich.console import Console

from atrace import trace_next_loaded_module
from atrace.core.analyzer import Filters, trace_to_history
from atrace.core.tracer import Trace
from atrace.reporter import history_to_table


def display_trace(trace: Trace):
    history = trace_to_history(trace, Filters.NO_EFFECT)
    trace_table = history_to_table(history)
    console = Console()
    console.print(trace_table)


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

    trace_next_loaded_module(display_trace)
    exec(compiled, module.__dict__)  # Execute code within the module's namespace
