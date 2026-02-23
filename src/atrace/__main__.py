import argparse
from types import ModuleType

from rich.console import Console

from . import Filters, Trace, trace_next_loaded_module, trace_to_history
from .reporter import history_to_table


def display_trace(trace: Trace):
    history = trace_to_history(trace, Filters.FUNCTION_ASSIGNMENT | Filters.NO_EFFECT)
    console = Console()
    console.print(history_to_table(history))


def run():
    parser = argparse.ArgumentParser(
        description="Displays the trace table of the given program"
    )
    parser.add_argument("program", help="The program you want the trace of.")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()
    compiled = compile(source, "", "exec")
    module = ModuleType("traced_module")

    trace_next_loaded_module(display_trace)
    exec(compiled, module.__dict__)  # Execute code within the module's namespace


if __name__ == "__main__":
    run()
