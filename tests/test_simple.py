import unittest
from unittest.mock import patch

from atrace import (
    UNASSIGN,
    Call,
    Filters,
    History,
    Line,
    Loc,
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
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 1), Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = []
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_single_assignment(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import single_assignment  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 3), Return({"x": 1}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_assign_none_unassign(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_none_unassign  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"x": 1}, {})),
            (Loc("<module>", 5), Line({"x": None}, {})),
            (Loc("<module>", 6), Line({}, {})),
            (Loc("<module>", 6), Return({"x": "bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {Var("<module>", "x"): None}, None),
            (Loc("<module>", 5), {Var("<module>", "x"): UNASSIGN}, None),
            (Loc("<module>", 6), {Var("<module>", "x"): "bob"}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_parallel_assignment(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import parallel_assignment  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 3), Return({"x": 1, "y": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (
                Loc("<module>", 3),
                {Var("<module>", "x"): 1, Var("<module>", "y"): 2},
                None,
            ),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import print as _print  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 3), Output("hello")),
            (Loc("<module>", 3), Output("\n")),
            (Loc("<module>", 3), Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (Loc("<module>", 3), {}, "hello\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_assign_then_print(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import assign_then_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"x": 1}, {})),
            (Loc("<module>", 4), Output("1")),
            (Loc("<module>", 4), Output("\n")),
            (Loc("<module>", 4), Return({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {}, "1\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_input(self):
        trace_next_loaded_module(self.callback_done)
        with patch("builtins.input", return_value="Bob"):
            from .snippets import input  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"x": "Bob"}, {})),
            (Loc("<module>", 4), Output("hello")),
            (Loc("<module>", 4), Output(" ")),
            (Loc("<module>", 4), Output("Bob")),
            (Loc("<module>", 4), Output("\n")),
            (Loc("<module>", 4), Return({"x": "Bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): "Bob"}, None),
            (Loc("<module>", 4), {}, "hello Bob\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_while_loop(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import while_loop  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"x": 0}, {})),
            (Loc("<module>", 5), Line({"x": 0}, {})),
            (Loc("<module>", 4), Line({"x": 1}, {})),
            (Loc("<module>", 5), Line({"x": 1}, {})),
            (Loc("<module>", 4), Line({"x": 2}, {})),
            (Loc("<module>", 4), Return({"x": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 0}, None),
            (Loc("<module>", 5), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 5), {Var("<module>", "x"): 2}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_for_with_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import for_with_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"i": 0}, {})),
            (Loc("<module>", 4), Output("0")),
            (Loc("<module>", 4), Output("\n")),
            (Loc("<module>", 3), Line({"i": 0}, {})),
            (Loc("<module>", 4), Line({"i": 1}, {})),
            (Loc("<module>", 4), Output("1")),
            (Loc("<module>", 4), Output("\n")),
            (Loc("<module>", 3), Line({"i": 1}, {})),
            (Loc("<module>", 4), Line({"i": 2}, {})),
            (Loc("<module>", 4), Output("2")),
            (Loc("<module>", 4), Output("\n")),
            (Loc("<module>", 3), Line({"i": 2}, {})),
            (Loc("<module>", 3), Return({"i": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "i"): 0}, None),
            (Loc("<module>", 4), {}, "0\n"),
            (Loc("<module>", 3), {Var("<module>", "i"): 1}, None),
            (Loc("<module>", 4), {}, "1\n"),
            (Loc("<module>", 3), {Var("<module>", "i"): 2}, None),
            (Loc("<module>", 4), {}, "2\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_loop_with_mutation_and_print(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import loop_with_mutation_and_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({"lst": ["a", "b"]}, {})),
            (Loc("<module>", 5), Line({"lst": ["a", "b"]}, {})),
            (Loc("<module>", 5), Output("a")),
            (Loc("<module>", 5), Output("\n")),
            (Loc("<module>", 4), Line({"lst": ["b"]}, {})),
            (Loc("<module>", 5), Line({"lst": ["b"]}, {})),
            (Loc("<module>", 5), Output("b")),
            (Loc("<module>", 5), Output("\n")),
            (Loc("<module>", 4), Line({"lst": []}, {})),
            (Loc("<module>", 4), Return({"lst": []}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "lst"): ["a", "b"]}, None),
            (Loc("<module>", 5), {Var("<module>", "lst"): ["b"]}, "a\n"),
            (Loc("<module>", 5), {Var("<module>", "lst"): []}, "b\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_list_comprehension(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import list_comprehension  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 3), Line({}, {"x": 0})),
            (Loc("<module>", 3), Line({}, {"x": 1})),
            (Loc("<module>", 3), Line({}, {"x": 2})),
            (Loc("<module>", 3), Line({}, {"x": 3})),
            (Loc("<module>", 3), Return({"lst": [0, 1, 4, 9]}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 0}, None),
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 3), {Var("<module>", "x"): 2}, None),
            (Loc("<module>", 3), {Var("<module>", "x"): 3}, None),
            (
                Loc("<module>", 3),
                {
                    Var("<module>", "x"): UNASSIGN,
                    Var("<module>", "lst"): [0, 1, 4, 9],
                },
                None,
            ),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_import(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import importing  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 6), Line({}, {})),
            (Loc("<module>", 6), Output("3.141592653589793")),
            (Loc("<module>", 6), Output("\n")),
            (Loc("<module>", 6), Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history: History = [
            (Loc("<module>", 6), {}, "3.141592653589793\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )
