import unittest

from atrace.model import (
    PrintEvent,
    ReturnEvent,
    TraceItem,
    Variable,
    VariableChangeEvent,
)
from atrace.reporter import Instant, trace_to_instants


class TestReporter(unittest.TestCase):
    def test_simple_assignments(self):
        trace = [
            TraceItem(
                line_no=1,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "x"), 1),
            ),
            TraceItem(
                line_no=2,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "y"), 2),
            ),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={Variable("<module>", "x"): 1},
                output="",
            ),
            Instant(
                line_no=2,
                variable_changes={Variable("<module>", "y"): 2},
                output="",
            ),
        ]

        self.assertEqual(expected, trace_to_instants(trace))

    def test_parallel_assignments(self):
        trace = [
            TraceItem(
                line_no=1,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "x"), 1),
            ),
            TraceItem(
                line_no=1,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "y"), 2),
            ),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={
                    Variable("<module>", "x"): 1,
                    Variable("<module>", "y"): 2,
                },
                output="",
            )
        ]
        self.assertEqual(expected, trace_to_instants(trace))

    def test_assignments_in_tight_loop(self):
        trace = [
            TraceItem(
                line_no=1,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "x"), 1),
            ),
            TraceItem(
                line_no=1,
                function_name="<module>",
                event=VariableChangeEvent(Variable("<module>", "x"), 2),
            ),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={Variable("<module>", "x"): 1},
                output="",
            ),
            Instant(
                line_no=1,
                variable_changes={Variable("<module>", "x"): 2},
                output="",
            ),
        ]
        self.assertEqual(expected, trace_to_instants(trace))

    def test_simple_output(self):
        trace = [
            TraceItem(line_no=1, function_name="<module>", event=PrintEvent("hello")),
            TraceItem(line_no=2, function_name="<module>", event=PrintEvent("world")),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={},
                output="hello",
            ),
            Instant(
                line_no=2,
                variable_changes={},
                output="world",
            ),
        ]
        self.assertEqual(expected, trace_to_instants(trace))

    def test_coalesce_output(self):
        trace = [
            TraceItem(line_no=1, function_name="<module>", event=PrintEvent("hello")),
            TraceItem(line_no=1, function_name="<module>", event=PrintEvent("world")),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={},
                output="helloworld",
            ),
        ]
        self.assertEqual(expected, trace_to_instants(trace))

    def no_test_return_value(self):  # XXX. We don't implement this yet
        trace = [
            TraceItem(
                line_no=1,
                function_name="f",
                event=VariableChangeEvent(Variable("f", "x"), 1),
            ),
            TraceItem(
                line_no=2,
                function_name="f",
                event=ReturnEvent("f>", "a return value"),
            ),
        ]

        expected = [
            Instant(
                line_no=1,
                variable_changes={Variable("f", "x"): 1},
                output="",
            ),
        ]

        self.assertEqual(expected, trace_to_instants(trace))
