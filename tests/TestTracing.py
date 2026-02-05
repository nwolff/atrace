import unittest

import atrace
from atrace.model import PrintEvent, TraceItem, Variable, VariableChangeEvent


class TestTracing(unittest.TestCase):
    def test_print(self):
        atrace.trace_next_loaded_module()

        from .programs import print as _print  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=3, function_name="<module>", event=PrintEvent(text="hello")
            ),
            TraceItem(line_no=3, function_name="<module>", event=PrintEvent(text="\n")),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_assign(self):
        atrace.trace_next_loaded_module()

        from .programs import assign  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=1
                ),
            )
        ]
        self.assertEqual(
            expected,
            atrace.trace,
        )

    def test_assign_and_print(self):
        atrace.trace_next_loaded_module()

        from .programs import assign_and_print  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()
        expected = [
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=1
                ),
            ),
            TraceItem(line_no=4, function_name="<module>", event=PrintEvent(text="1")),
            TraceItem(line_no=4, function_name="<module>", event=PrintEvent(text="\n")),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_assign_print_assign(self):
        atrace.trace_next_loaded_module()

        from .programs import assign_print_assign  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=1
                ),
            ),
            TraceItem(line_no=4, function_name="<module>", event=PrintEvent(text="1")),
            TraceItem(line_no=4, function_name="<module>", event=PrintEvent(text="\n")),
            TraceItem(
                line_no=5,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="y"), value=1
                ),
            ),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_parallel_assignment(self):
        atrace.trace_next_loaded_module()

        from .programs import parallel_assignment  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=1
                ),
            ),
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="y"), value=2
                ),
            ),
        ]
        self.assertEqual(expected, atrace.trace)

    def test_tight_loop(self):
        atrace.trace_next_loaded_module()

        from .programs import tight_loop  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=3,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=0
                ),
            ),
            TraceItem(
                line_no=6,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=1
                ),
            ),
            TraceItem(
                line_no=6,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=2
                ),
            ),
        ]
        self.assertEqual(expected, atrace.trace)
