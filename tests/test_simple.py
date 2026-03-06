import unittest
from unittest.mock import patch

from atrace import (
    UNASSIGN,
    Call,
    History,
    Line,
    Meta,
    Output,
    Return,
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
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (1, Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [(1, {}, None, Meta.NONE)]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_single_assignment(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import single_assignment  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (3, Return({"x": 1}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 1}, None, Meta.NONE),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_assign_none_unassign(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_none_unassign  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"x": 1}, {})),
            (5, Line({"x": None}, {})),
            (6, Line({}, {})),
            (6, Return({"x": "bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (4, {Var("<module>", "x"): None}, None, Meta.NONE),
            (5, {Var("<module>", "x"): UNASSIGN}, None, Meta.NONE),
            (6, {Var("<module>", "x"): "bob"}, None, Meta.NONE),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace),
        )

    def test_parallel_assignment(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import parallel_assignment  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (3, Return({"x": 1, "y": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (
                3,
                {Var("<module>", "x"): 1, Var("<module>", "y"): 2},
                None,
                Meta.NONE,
            ),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import print as _print  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (3, Output("hello")),
            (3, Output("\n")),
            (3, Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, {}, None, Meta.NONE),
            (3, {}, "hello\n", Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_assign_then_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_then_print  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"x": 1}, {})),
            (4, Output("1")),
            (4, Output("\n")),
            (4, Return({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (4, {}, "1\n", Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_input(self):
        trace_next_loaded_module(self.callback_done)
        with patch("builtins.input", return_value="Bob"):
            from .snippets import input  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"x": "Bob"}, {})),
            (4, Output("hello")),
            (4, Output(" ")),
            (4, Output("Bob")),
            (4, Output("\n")),
            (4, Return({"x": "Bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): "Bob"}, None, Meta.NONE),
            (4, {}, "hello Bob\n", Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_while_loop(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import while_loop  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"x": 0}, {})),
            (5, Line({"x": 0}, {})),
            (4, Line({"x": 1}, {})),
            (5, Line({"x": 1}, {})),
            (4, Line({"x": 2}, {})),
            (4, Return({"x": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 0}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
            (5, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
            (5, {Var("<module>", "x"): 2}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_for_with_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import for_with_print  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"i": 0}, {})),
            (4, Output("0")),
            (4, Output("\n")),
            (3, Line({"i": 0}, {})),
            (4, Line({"i": 1}, {})),
            (4, Output("1")),
            (4, Output("\n")),
            (3, Line({"i": 1}, {})),
            (4, Line({"i": 2}, {})),
            (4, Output("2")),
            (4, Output("\n")),
            (3, Line({"i": 2}, {})),
            (3, Return({"i": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "i"): 0}, None, Meta.NONE),
            (4, {}, "0\n", Meta.NONE),
            (3, {Var("<module>", "i"): 1}, None, Meta.NONE),
            (4, {}, "1\n", Meta.NONE),
            (3, {Var("<module>", "i"): 2}, None, Meta.NONE),
            (4, {}, "2\n", Meta.NONE),
            (3, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_loop_with_mutation_and_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import loop_with_mutation_and_print  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"lst": ["a", "b"]}, {})),
            (5, Line({"lst": ["a", "b"]}, {})),
            (5, Output("a")),
            (5, Output("\n")),
            (4, Line({"lst": ["b"]}, {})),
            (5, Line({"lst": ["b"]}, {})),
            (5, Output("b")),
            (5, Output("\n")),
            (4, Line({"lst": []}, {})),
            (4, Return({"lst": []}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "lst"): ["a", "b"]}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
            (5, {Var("<module>", "lst"): ["b"]}, "a\n", Meta.NONE),
            (4, {}, None, Meta.NONE),
            (5, {Var("<module>", "lst"): []}, "b\n", Meta.NONE),
            (4, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_list_comprehension(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import list_comprehension  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (3, Line({}, {"x": 0})),
            (3, Line({}, {"x": 1})),
            (3, Line({}, {"x": 2})),
            (3, Line({}, {"x": 3})),
            (3, Return({"lst": [0, 1, 4, 9]}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 0}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 2}, None, Meta.NONE),
            (3, {Var("<module>", "x"): 3}, None, Meta.NONE),
            (
                3,
                {
                    Var("<module>", "x"): UNASSIGN,
                    Var("<module>", "lst"): [0, 1, 4, 9],
                },
                None,
                Meta.NONE,
            ),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_import(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import importing  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({}, {})),
            (6, Line({}, {})),
            (6, Output("3.141592653589793")),
            (6, Output("\n")),
            (6, Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (1, {}, None, Meta.NONE),
            (3, {}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
            (6, {}, "3.141592653589793\n", Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
