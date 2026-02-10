import unittest

import atrace
from atrace.model import CallEvent, LineEvent, OutputEvent, ReturnEvent, TraceItem


class TestTracingWithFunctions(unittest.TestCase):
    def test_simple_function(self):
        atrace.trace_next_loaded_module()

        from .programs import function  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=4, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=9, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=4, function_name="double", event=CallEvent(locals={"a": 3})
            ),
            TraceItem(
                line_no=5, function_name="double", event=LineEvent(locals={"a": 3})
            ),
            TraceItem(
                line_no=6,
                function_name="double",
                event=LineEvent(locals={"a": 3, "result": 6}),
            ),
            TraceItem(
                line_no=6,
                function_name="double",
                event=ReturnEvent(locals={"a": 3, "result": 6}, return_value=6),
            ),
            TraceItem(
                line_no=9,
                function_name="<module>",
                event=ReturnEvent(locals={"x": 6}, return_value=None),
            ),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_function_with_recursion(self):
        atrace.trace_next_loaded_module()

        from .programs import function_with_recursion  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=4, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=8, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=4, function_name="sum_up_to", event=CallEvent(locals={"x": 3})
            ),
            TraceItem(
                line_no=5, function_name="sum_up_to", event=LineEvent(locals={"x": 3})
            ),
            TraceItem(
                line_no=4, function_name="sum_up_to", event=CallEvent(locals={"x": 2})
            ),
            TraceItem(
                line_no=5, function_name="sum_up_to", event=LineEvent(locals={"x": 2})
            ),
            TraceItem(
                line_no=4, function_name="sum_up_to", event=CallEvent(locals={"x": 1})
            ),
            TraceItem(
                line_no=5, function_name="sum_up_to", event=LineEvent(locals={"x": 1})
            ),
            TraceItem(
                line_no=4, function_name="sum_up_to", event=CallEvent(locals={"x": 0})
            ),
            TraceItem(
                line_no=5, function_name="sum_up_to", event=LineEvent(locals={"x": 0})
            ),
            TraceItem(
                line_no=5,
                function_name="sum_up_to",
                event=ReturnEvent(locals={"x": 0}, return_value=0),
            ),
            TraceItem(
                line_no=5,
                function_name="sum_up_to",
                event=ReturnEvent(locals={"x": 1}, return_value=1),
            ),
            TraceItem(
                line_no=5,
                function_name="sum_up_to",
                event=ReturnEvent(locals={"x": 2}, return_value=3),
            ),
            TraceItem(
                line_no=5,
                function_name="sum_up_to",
                event=ReturnEvent(locals={"x": 3}, return_value=6),
            ),
            TraceItem(
                line_no=8,
                function_name="<module>",
                event=ReturnEvent(locals={"result": 6}, return_value=None),
            ),
        ]

        self.assertEqual(expected, atrace.trace)
