import unittest
from unittest import mock

from atrace import (
    UNASSIGN,
    Line,
    Raise,
    TCall,
    TException,
    TLine,
    TOutput,
    TReturn,
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
            (0, TCall({}, {}, "<module>")),
            (2, TLine({}, {})),
            (4, TLine({}, {})),
            (6, TLine({"x": 1}, {})),
            (
                6,
                TException({"x": 1}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (6, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (2, Line({}, None)),
            (4, Line({Var("<module>", "x"): 1}, None)),
            (6, Line({}, None)),
            (6, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_uncaught_exception(self):
        trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .snippets import uncaught_exception  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (3, TOutput("hai\n")),
            (4, TLine({}, {})),
            (5, TLine({"x": 1}, {})),
            (
                5,
                TException(
                    {"x": 1},
                    {},
                    mock.ANY,
                    mock.ANY,
                    mock.ANY,
                ),
            ),
            (5, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({}, "hai\n")),
            (4, Line({Var("<module>", "x"): 1}, None)),
            (5, Line({}, None)),
            (5, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_caught_exception(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import caught_exception  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({}, {})),
            (
                4,
                TException({}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (5, TLine({}, {})),
            (6, TLine({"e": mock.ANY}, {})),
            (6, TOutput("error message\n")),
            (6, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({}, None)),
            (4, Line({}, None)),
            (4, Raise(mock.ANY, mock.ANY, mock.ANY)),
            (5, Line({Var("<module>", "e"): mock.ANY}, None)),
            (6, Line({Var("<module>", "e"): UNASSIGN}, "error message\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
