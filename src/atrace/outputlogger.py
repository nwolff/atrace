import sys
from typing import TextIO

from . import vartracer


class OutputLogger:
    """
    OutputLogger wraps stdout, passing down writes and flushes to it, while simultaneously capturing the text to the trace.
    """

    def __init__(self, trace: vartracer.Trace, stdout: TextIO):
        self.trace = trace
        self.stdout = stdout

    def write(self, text: str) -> None:
        """
        Write to stdout and also record the text in the trace
        """
        self.stdout.write(text)

        frame = sys._getframe(1)

        self.trace.append(
            vartracer.TraceItem(
                line_no=frame.f_lineno,
                function_name=frame.f_code.co_name,
                event=vartracer.OutputEvent(text),
            )
        )

    def flush(self):
        self.stdout.flush()
