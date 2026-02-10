import unittest

import atrace
from atrace.model import CallEvent, LineEvent, OutputEvent, ReturnEvent, TraceItem


class TestTracingSimple(unittest.TestCase):
    def test_assign(self):
        atrace.trace_next_loaded_module()

        from .programs import assign  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=3, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=ReturnEvent(locals={"x": 1}, return_value=None),
            ),
        ]

        self.assertEqual(
            expected,
            atrace.trace,
        )

    def test_print(self):
        atrace.trace_next_loaded_module()

        from .programs import print as _print  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=3, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=3, function_name="<module>", event=OutputEvent(text="hello")
            ),
            TraceItem(
                line_no=3, function_name="<module>", event=OutputEvent(text="\n")
            ),
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=ReturnEvent(locals={}, return_value=None),
            ),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_assign_and_print(self):
        atrace.trace_next_loaded_module()

        from .programs import assign_and_print  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=3, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=4, function_name="<module>", event=LineEvent(locals={"x": 1})
            ),
            TraceItem(line_no=4, function_name="<module>", event=OutputEvent(text="1")),
            TraceItem(
                line_no=4, function_name="<module>", event=OutputEvent(text="\n")
            ),
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=ReturnEvent(locals={"x": 1}, return_value=None),
            ),
        ]

        self.assertEqual(expected, atrace.trace)

    def test_loop_with_mutation_and_print(self):
        atrace.trace_next_loaded_module()

        from .programs import loop_with_mutation_and_print  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(line_no=0, function_name="<module>", event=CallEvent(locals={})),
            TraceItem(line_no=1, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(line_no=3, function_name="<module>", event=LineEvent(locals={})),
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["a", "b"]}),
            ),
            TraceItem(
                line_no=5,
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
            TraceItem(
                line_no=5,
                function_name="<module>",
                event=LineEvent(locals={"lst": ["b"]}),
            ),
            TraceItem(line_no=5, function_name="<module>", event=OutputEvent(text="b")),
            TraceItem(
                line_no=5, function_name="<module>", event=OutputEvent(text="\n")
            ),
            TraceItem(
                line_no=4, function_name="<module>", event=LineEvent(locals={"lst": []})
            ),
            TraceItem(
                line_no=4,
                function_name="<module>",
                event=ReturnEvent(locals={"lst": []}, return_value=None),
            ),
        ]

        self.assertEqual(expected, atrace.trace)
