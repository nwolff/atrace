import unittest

import atrace
from atrace.model import TraceItem, Variable, VariableChangeEvent


class TestTracingWithFunctions(unittest.TestCase):
    def no_test_function(self):  # XXX
        atrace.trace_next_loaded_module()

        from .programs import function  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

        expected = [
            TraceItem(
                line_no=4,
                function_name="double",
                event=VariableChangeEvent(
                    variable=Variable(scope="double", name="a"), value=3
                ),
            ),
            TraceItem(
                line_no=5,
                function_name="double",
                event=VariableChangeEvent(
                    variable=Variable(scope="double", name="result"), value=6
                ),
            ),
            TraceItem(
                line_no=9,
                function_name="<module>",
                event=VariableChangeEvent(
                    variable=Variable(scope="<module>", name="x"), value=6
                ),
            ),
        ]

        self.assertEqual(expected, atrace.trace)
