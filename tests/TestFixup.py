import unittest

from atrace.fixup import coalesce_outputs
from atrace.vartracer import CallEvent, LineEvent, OutputEvent, ReturnEvent, TraceItem


class TestFixup(unittest.TestCase):
    def test_coalesce_output(self):
        trace = [
            TraceItem(
                line_no=3, function_name="<module>", event=OutputEvent(text="hello")
            ),
            TraceItem(
                line_no=3, function_name="<module>", event=OutputEvent(text="\n")
            ),
        ]
        expected = [
            TraceItem(
                line_no=3, function_name="<module>", event=OutputEvent(text="hello\n")
            ),
        ]

        self.assertEqual(expected, coalesce_outputs(trace))

    def test_dont_coalesce_in_loop(self):
        trace = [
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["a", "b"]}),
            ),
            TraceItem(line_no=5, function_name="<module>", event=OutputEvent(text="a")),
            TraceItem(
                line_no=5, function_name="<module>", event=OutputEvent(text="\n")
            ),
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["b"]}),
            ),
            TraceItem(line_no=5, function_name="<module>", event=OutputEvent(text="b")),
            TraceItem(
                line_no=5, function_name="<module>", event=OutputEvent(text="\n")
            ),
        ]

        expected = [
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["a", "b"]}),
            ),
            TraceItem(
                line_no=5, function_name="<module>", event=OutputEvent(text="a\n")
            ),
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["b"]}),
            ),
            TraceItem(
                line_no=5, function_name="<module>", event=OutputEvent(text="b\n")
            ),
        ]

        self.assertEqual(expected, coalesce_outputs(trace))
