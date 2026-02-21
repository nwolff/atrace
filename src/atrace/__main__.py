import argparse
from types import ModuleType
from . import dump_report, trace_next_loaded_module

parser = argparse.ArgumentParser(
    description="Displays the trace table of the given program"
)
parser.add_argument("program", help="The program you want the trace of.")
options = parser.parse_args()

with open(options.program, "r") as content_file:
    content = content_file.read()
compiled = compile(content, "", "exec")
module = ModuleType("traced_module")

trace_next_loaded_module(dump_report)
exec(compiled, module.__dict__) # Execute code within the module's namespace
