import argparse
import re

from . import Trace, trace_code
from .interpreter import trace_to_history
from .reporter import LeftAligned, TableData, history_to_table_data


def escape_markdown(text: str) -> str:
    """
    Escapes special Markdown characters in a string.
    """
    # List of Markdown special characters that need escaping
    # Order matters: backslash must be escaped first
    parse_chars = r"([\\`*_{}\[\]()#+-.!|])"

    # Substitutes the matched character with a backslash and the character itself
    return re.sub(parse_chars, r"\\\1", text)


def table_data_to_typst(table_data: TableData) -> str:
    result = []

    headers, rows = table_data

    # Table
    result.append("#table(\n")

    # Columns
    result.append("columns: (")
    for header in headers:
        result.append("1fr, ")
    result.append("),\n")

    # First row, with emphasis
    for header in headers:
        match header:
            case LeftAligned(s):
                pass
            case str(s):
                pass
        result.append(f"[*{escape_markdown(s)}*], ")
    result.append("\n")

    # The content of each cell
    for row in rows:
        for index, item in enumerate(row):
            result.append('"' + escape_markdown(item) + '"' + ", ")
        result.append("\n")

    # Close the table
    result.append(")")

    return "".join(result)


def run():
    parser = argparse.ArgumentParser(
        description="Displays a markdown output of the trace of the given program."
    )
    parser.add_argument("program", help="The path to a python file")
    options = parser.parse_args()

    with open(options.program) as content_file:
        source = content_file.read()

    def on_trace(trace: Trace) -> None:
        history = trace_to_history(trace)
        table_data = history_to_table_data(history)
        typst = table_data_to_typst(table_data)
        print()  # To separate the typst markup from the program output
        print(typst)

    trace_code(source, on_trace)


if __name__ == "__main__":
    run()
