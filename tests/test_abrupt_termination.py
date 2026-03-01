import unittest
from unittest import mock

from atrace import (
    UNASSIGN,
    Call,
    ExceptionOccurred,
    Filters,
    Line,
    Loc,
    Output,
    Return,
    Var,
    trace_next_loaded_module,
    trace_to_history,
)


class TestAbruptTermination(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_syntax_error(self):
        trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .snippets import syntax_error  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 2), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 6), Line({"x": 1}, {})),
            (
                Loc("<module>", 6),
                ExceptionOccurred({"x": 1}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (Loc("<module>", 6), Return({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [(Loc("<module>", 4), {Var("<module>", "x"): 1}, None)]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_uncaught_exception(self):
        trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .snippets import uncaught_exception  # noqa

        expected_history = [
            (Loc("<module>", 3), {}, "hai\n"),
            (Loc("<module>", 4), {Var("<module>", "x"): 1}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_caught_exception(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import caught_exception  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (
                Loc("<module>", 4),
                ExceptionOccurred({}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (Loc("<module>", 5), Line({}, {})),
            (Loc("<module>", 6), Line({"e": mock.ANY}, {})),
            (Loc("<module>", 6), Output("error message")),
            (Loc("<module>", 6), Output("\n")),
            (Loc("<module>", 6), Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 5), {Var("<module>", "e"): mock.ANY}, None),
            (Loc("<module>", 6), {Var("<module>", "e"): UNASSIGN}, "error message\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )
