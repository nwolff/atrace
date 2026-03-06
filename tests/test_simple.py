import unittest
from unittest.mock import patch

from atrace import (
    UNASSIGN,
    History,
    Line,
    TCall,
    TLine,
    TOutput,
    TReturn,
    Var,
    trace_next_loaded_module,
    trace_to_history,
)


class TestSimple(unittest.TestCase):
    """
    Test everything that does not involve functions
    """

    def callback_done(self, trace):
        self.trace = trace

    def test_empty(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import empty  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [(1, Line({}, None))]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_single_assignment(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import single_assignment  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TReturn({"x": 1}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 1}, None)),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_assign_none_unassign(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_none_unassign  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"x": 1}, {})),
            (5, TLine({"x": None}, {})),
            (6, TLine({}, {})),
            (6, TReturn({"x": "bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 1}, None)),
            (4, Line({Var("<module>", "x"): None}, None)),
            (5, Line({Var("<module>", "x"): UNASSIGN}, None)),
            (6, Line({Var("<module>", "x"): "bob"}, None)),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_parallel_assignment(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import parallel_assignment  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TReturn({"x": 1, "y": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 1, Var("<module>", "y"): 2}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import print as _print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TOutput("hello world!\n")),
            (4, TLine({}, {})),
            (4, TOutput("goodbye\n")),
            (4, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, Line({}, None)),
            (3, Line({}, "hello world!\n")),
            (4, Line({}, "goodbye\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_assign_then_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_then_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"x": 1}, {})),
            (4, TOutput("1\n")),
            (4, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 1}, None)),
            (4, Line({}, "1\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_input(self):
        """In this test it looks like the prompt does not appear in the trace.
        In real code it does.
        I tried to use side_effect with patch, but then the side effect function
        invocation appears in the trace."""
        trace_next_loaded_module(self.callback_done)

        with patch("builtins.input", return_value="Bob"):
            from .snippets import input  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"x": "Bob"}, {})),
            (4, TOutput("Hello Bob\n")),
            (4, TReturn({"x": "Bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): "Bob"}, None)),
            (4, Line({}, "Hello Bob\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_while_loop(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import while_loop  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"x": 0}, {})),
            (5, TLine({"x": 0}, {})),
            (4, TLine({"x": 1}, {})),
            (5, TLine({"x": 1}, {})),
            (4, TLine({"x": 2}, {})),
            (4, TReturn({"x": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 0}, None)),
            (4, Line({}, None)),
            (5, Line({Var("<module>", "x"): 1}, None)),
            (4, Line({}, None)),
            (5, Line({Var("<module>", "x"): 2}, None)),
            (4, Line({}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_for_with_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import for_with_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"i": 0}, {})),
            (4, TOutput("0\n")),
            (3, TLine({"i": 0}, {})),
            (4, TLine({"i": 1}, {})),
            (4, TOutput("1\n")),
            (3, TLine({"i": 1}, {})),
            (4, TLine({"i": 2}, {})),
            (4, TOutput("2\n")),
            (3, TLine({"i": 2}, {})),
            (3, TReturn({"i": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "i"): 0}, None)),
            (4, Line({}, "0\n")),
            (3, Line({Var("<module>", "i"): 1}, None)),
            (4, Line({}, "1\n")),
            (3, Line({Var("<module>", "i"): 2}, None)),
            (4, Line({}, "2\n")),
            (3, Line({}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_loop_with_mutation_and_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import loop_with_mutation_and_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"lst": ["a", "b"]}, {})),
            (5, TLine({"lst": ["a", "b"]}, {})),
            (5, TOutput("a\n")),
            (4, TLine({"lst": ["b"]}, {})),
            (5, TLine({"lst": ["b"]}, {})),
            (5, TOutput("b\n")),
            (4, TLine({"lst": []}, {})),
            (4, TReturn({"lst": []}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "lst"): ["a", "b"]}, None)),
            (4, Line({}, None)),
            (5, Line({Var("<module>", "lst"): ["b"]}, "a\n")),
            (4, Line({}, None)),
            (5, Line({Var("<module>", "lst"): []}, "b\n")),
            (4, Line({}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_list_comprehension(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import list_comprehension  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TLine({}, {"x": 0})),
            (3, TLine({}, {"x": 1})),
            (3, TLine({}, {"x": 2})),
            (3, TLine({}, {"x": 3})),
            (3, TReturn({"lst": [0, 1, 4, 9]}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 0}, None)),
            (3, Line({Var("<module>", "x"): 1}, None)),
            (3, Line({Var("<module>", "x"): 2}, None)),
            (3, Line({Var("<module>", "x"): 3}, None)),
            (
                3,
                Line(
                    {
                        Var("<module>", "lst"): [0, 1, 4, 9],
                        Var("<module>", "x"): UNASSIGN,
                    },
                    None,
                ),
            ),
        ]

        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_one_line_for_loop(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import one_line_for_loop  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (2, TLine({}, {})),
            (2, TOutput("0\n")),
            (2, TLine({"i": 0}, {})),
            (2, TOutput("1\n")),
            (2, TLine({"i": 1}, {})),
            (2, TReturn({"i": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (2, Line(assignments={Var(scope="<module>", name="i"): 0}, output="0\n")),
            (2, Line(assignments={Var(scope="<module>", name="i"): 1}, output="1\n")),
            (2, Line(assignments={}, output=None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_one_line_three_statements(self):
        """One cannot see the details of what happens inside a line"""
        trace_next_loaded_module(self.callback_done)

        from .snippets import one_line_three_statements  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (2, TLine({}, {})),
            (2, TOutput("15\nha\n")),
            (2, TReturn({"x": 3, "y": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (
                2,
                Line({Var("<module>", "y"): 10, Var("<module>", "x"): 3}, "15\nha\n"),
            )
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_import(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import importing  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({}, {})),
            (6, TLine({}, {})),
            (6, TOutput("3.141592653589793\n")),
            (6, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, Line({}, None)),
            (3, Line({}, None)),
            (4, Line({}, None)),
            (6, Line({}, "3.141592653589793\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
