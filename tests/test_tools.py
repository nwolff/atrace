import textwrap
import unittest

from atrace import trace_next_loaded_module
from atrace.interpreter import trace_to_history
from atrace.reporter import history_to_table_data
from atrace.typst import table_data_to_typst


class TestTypst(unittest.TestCase):
    def on_trace(self, trace):
        self.trace = trace

    def test_array_access(self):
        """
        Array access was designed to show markdown edge cases
        """
        trace_next_loaded_module(self.on_trace)
        from .snippets import array_access  # noqa

        history = trace_to_history(self.trace)
        table_data = history_to_table_data(history)

        expected_typst_raw = r"""\
        #table(
        columns: (1fr, 1fr, 1fr, 1fr, 1fr, ),
        [*line*], [*print\_each*], [*\(print\_each\) lst*], [*\(print\_each\) i*], [*output*], 
        "1", "print\_each\(\["a"\, "b"\, "c"\]\)", "\["a"\, "b"\, "c"\]", "", "", 
        "2", "│  ", "", "0", "", 
        "3", "│  ", "", "", "lst\[0\]=a", 
        "2", "│  ", "", "1", "", 
        "3", "│  ", "", "", "lst\[1\]=b", 
        "2", "│  ", "", "2", "", 
        "3", "│  ", "", "", "lst\[2\]=c", 
        "2", "└─ ", "", "", "", 
        )"""  # noqa: E501, W291
        expected_typst = textwrap.dedent(expected_typst_raw[2:])

        self.assertEqual(expected_typst, table_data_to_typst(table_data))
