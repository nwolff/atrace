import unittest
from unittest.mock import patch

from atrace import (
    TCall,
    TLine,
    TOutput,
    TReturn,
    trace_next_loaded_module,
)
from atrace.interpreter import (
    UNASSIGN,
    History,
    Line,
    LineEffects,
    Var,
    trace_to_history,
)


class TestSimple(unittest.TestCase):
    """
    Test code that does not involve functions or exceptions.
    """

    def on_trace(self, trace):
        self.trace = trace

    def test_empty(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import empty  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (0, TLine({}, {})),
            (0, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [(0, Line())]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_single_assignment(self):
        trace_next_loaded_module(self.on_trace)
        from .snippets import single_assignment  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TReturn({"x": 1}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_assign_none_unassign(self):
        trace_next_loaded_module(self.on_trace)
        from .snippets import assign_none_unassign  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"x": 1}, {})),
            (3, TLine({"x": None}, {})),
            (4, TLine({}, {})),
            (4, TReturn({"x": "bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (2, Line()),
            (2, LineEffects({Var("<module>", "x"): None}, None)),
            (3, Line()),
            (3, LineEffects({Var("<module>", "x"): UNASSIGN}, None)),
            (4, Line()),
            (4, LineEffects({Var("<module>", "x"): "bob"}, None)),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_parallel_assignment(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import parallel_assignment  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TReturn({"x": 1, "y": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1, Var("<module>", "y"): 2}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_print(self):
        trace_next_loaded_module(self.on_trace)
        from .snippets import print as _print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TOutput("hello world!\n")),
            (2, TLine({}, {})),
            (2, TOutput("goodbye\n")),
            (2, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, Line()),
            (1, LineEffects({}, "hello world!\n")),
            (2, Line()),
            (2, LineEffects({}, "goodbye\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_assign_then_print(self):
        trace_next_loaded_module(self.on_trace)
        from .snippets import assign_then_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"x": 1}, {})),
            (2, TOutput("1\n")),
            (2, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (2, Line()),
            (2, LineEffects({}, "1\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_input(self):
        # In this test it looks like the prompt does not appear in the trace.
        # In real code it does.
        # I tried to use side_effect with patch, but then the side effect function
        # invocation appears in the trace.
        trace_next_loaded_module(self.on_trace)

        with patch("builtins.input", return_value="Bob"):
            from .snippets import input  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"x": "Bob"}, {})),
            (2, TOutput("Hello Bob\n")),
            (2, TReturn({"x": "Bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): "Bob"}, None)),
            (2, Line()),
            (2, LineEffects({}, "Hello Bob\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_while_loop(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import while_loop  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"x": 0}, {})),
            (3, TLine({"x": 0}, {})),
            (2, TLine({"x": 1}, {})),
            (3, TLine({"x": 1}, {})),
            (2, TLine({"x": 2}, {})),
            (2, TReturn({"x": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 0}, None)),
            (2, Line()),
            (3, Line()),
            (3, LineEffects({Var("<module>", "x"): 1}, None)),
            (2, Line()),
            (3, Line()),
            (3, LineEffects({Var("<module>", "x"): 2}, None)),
            (2, Line()),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_while_with_print(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import reverse  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({"letters": ["a", "a"]}, {})),
            (4, TLine({"letters": ["a", "a"]}, {})),
            (5, TLine({"letters": ["a"], "letter": "a"}, {})),
            (5, TOutput("a\n")),
            (3, TLine({"letters": ["a"], "letter": "a"}, {})),
            (4, TLine({"letters": ["a"], "letter": "a"}, {})),
            (5, TLine({"letters": [], "letter": "a"}, {})),
            (5, TOutput("a\n")),
            (3, TLine({"letters": [], "letter": "a"}, {})),
            (3, TReturn({"letters": [], "letter": "a"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "letters"): ["a", "a"]}, None)),
            (3, Line()),
            (4, Line()),
            (
                4,
                LineEffects(
                    {Var("<module>", "letters"): ["a"], Var("<module>", "letter"): "a"},
                    None,
                ),
            ),
            (5, Line()),
            (5, LineEffects({}, "a\n")),
            (3, Line()),
            (4, Line()),
            # This is not a bug, `letter` is again "a" so there is no assignment to it
            (4, LineEffects({Var("<module>", "letters"): []}, None)),
            (5, Line()),
            (5, LineEffects({}, "a\n")),
            (3, Line()),
        ]

        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_for_with_print(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import for_with_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"i": 0}, {})),
            (2, TOutput("0\n")),
            (1, TLine({"i": 0}, {})),
            (2, TLine({"i": 1}, {})),
            (2, TOutput("1\n")),
            (1, TLine({"i": 1}, {})),
            (2, TLine({"i": 2}, {})),
            (2, TOutput("2\n")),
            (1, TLine({"i": 2}, {})),
            (1, TReturn({"i": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "i"): 0}, None)),
            (2, Line()),
            (2, LineEffects({}, "0\n")),
            (1, Line()),
            (1, LineEffects({Var("<module>", "i"): 1}, None)),
            (2, Line()),
            (2, LineEffects({}, "1\n")),
            (1, Line()),
            (1, LineEffects({Var("<module>", "i"): 2}, None)),
            (2, Line()),
            (2, LineEffects({}, "2\n")),
            (1, Line()),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_loop_with_mutation_and_print(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import loop_with_mutation_and_print  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"lst": ["a", "b"]}, {})),
            (3, TLine({"lst": ["a", "b"]}, {})),
            (3, TOutput("a\n")),
            (2, TLine({"lst": ["b"]}, {})),
            (3, TLine({"lst": ["b"]}, {})),
            (3, TOutput("b\n")),
            (2, TLine({"lst": []}, {})),
            (2, TReturn({"lst": []}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "lst"): ["a", "b"]}, None)),
            (2, Line()),
            (3, Line()),
            (3, LineEffects({Var("<module>", "lst"): ["b"]}, "a\n")),
            (2, Line()),
            (3, Line()),
            (3, LineEffects({Var("<module>", "lst"): []}, "b\n")),
            (2, Line()),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_list_comprehension(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import list_comprehension  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TLine({}, {"x": 0})),
            (1, TLine({}, {"x": 1})),
            (1, TLine({}, {"x": 2})),
            (1, TReturn({"lst": [0, 1, 4]}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 0}, None)),
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 2}, None)),
            (1, Line()),
            (
                1,
                LineEffects(
                    {Var("<module>", "lst"): [0, 1, 4], Var("<module>", "x"): UNASSIGN},
                    None,
                ),
            ),
        ]

        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_one_line_for_loop(self):
        trace_next_loaded_module(self.on_trace)

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
            (2, Line()),
            (2, LineEffects({Var("<module>", "i"): 0}, "0\n")),
            (2, Line()),
            (2, LineEffects({Var("<module>", "i"): 1}, "1\n")),
            (2, Line()),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_one_line_three_statements(self):
        """One cannot see the details of what happens inside a line"""
        trace_next_loaded_module(self.on_trace)

        from .snippets import one_line_three_statements  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (2, TLine({}, {})),
            (2, TOutput("15\nha\n")),
            (2, TReturn({"x": 3, "y": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (2, Line()),
            (
                2,
                LineEffects(
                    {Var("<module>", "y"): 10, Var("<module>", "x"): 3}, "15\nha\n"
                ),
            ),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_import(self):
        trace_next_loaded_module(self.on_trace)

        from .snippets import importing  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TOutput("3.141592653589793\n")),
            (3, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, Line()),
            (3, Line()),
            (3, LineEffects({}, "3.141592653589793\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
