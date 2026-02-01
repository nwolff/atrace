import sys
from typing import TextIO

from . import model


class OutputLogger:
    """
    OutputLogger wraps stdout, writing to it and simultaneously capturing the text to the trace.
    """

    def __init__(self, trace: model.Trace, stdout: TextIO):
        self.trace = trace
        self.stdout = stdout

    def write(self, text: str) -> None:
        """
        Write to stdout and record the text in the trace
        """
        self.stdout.write(text)

        frame = sys._getframe(1)
        # An alternative that uses a public API, but then the type checker bothers me
        # frame = inspect.currentframe().f_back

        self.trace.append(
            model.TraceItem(
                line_no=frame.f_lineno,
                function_name=frame.f_code.co_name,
                event=model.PrintEvent(text),
            )
        )

    def flush(self):
        self.stdout.flush()
