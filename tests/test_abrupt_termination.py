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
            (1, TLine({}, {})),
            (3, TLine({"x": 1}, {})),
            (
                3,
                TException({"x": 1}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (3, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({Var("<module>", "x"): 1}, None)),
            (3, Line({}, None)),
            (3, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_uncaught_exception(self):
        trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .snippets import uncaught_exception  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (1, TOutput("hai\n")),
            (2, TLine({}, {})),
            (3, TLine({"x": 1}, {})),
            (
                3,
                TException(
                    {"x": 1},
                    {},
                    mock.ANY,
                    mock.ANY,
                    mock.ANY,
                ),
            ),
            (3, TReturn({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, "hai\n")),
            (2, Line({Var("<module>", "x"): 1}, None)),
            (3, Line({}, None)),
            (3, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_caught_exception(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import caught_exception  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({}, {})),
            (
                2,
                TException({}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (3, TLine({}, {})),
            (4, TLine({"e": mock.ANY}, {})),
            (4, TOutput("error message\n")),
            (4, TReturn({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (2, Line({}, None)),
            (2, Raise(mock.ANY, mock.ANY, mock.ANY)),
            (3, Line({Var("<module>", "e"): mock.ANY}, None)),
            (4, Line({Var("<module>", "e"): UNASSIGN}, "error message\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
