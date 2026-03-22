import unittest
from unittest import mock

from atrace import (
    TCall,
    TException,
    TLine,
    TOutput,
    TReturn,
    trace_next_loaded_module,
)
from atrace.interpreter import (
    UNASSIGN,
    Line,
    LineEffects,
    Raise,
    Var,
    trace_to_history,
)


class TestAbruptTermination(unittest.TestCase):
    def on_trace(self, trace):
        self.trace = trace

    def test_syntax_error(self):
        trace_next_loaded_module(self.on_trace)

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
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (3, Line()),
            (3, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_uncaught_exception(self):
        trace_next_loaded_module(self.on_trace)

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
            (1, Line()),
            (1, LineEffects({}, "hai\n")),
            (2, Line()),
            (2, LineEffects({Var("<module>", "x"): 1}, None)),
            (3, Line()),
            (3, Raise(mock.ANY, mock.ANY, mock.ANY)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_caught_exception(self):
        trace_next_loaded_module(self.on_trace)

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
            (1, Line()),
            (2, Line()),
            (2, Raise(mock.ANY, mock.ANY, mock.ANY)),
            (3, Line()),
            (3, LineEffects({Var("<module>", "e"): mock.ANY}, None)),
            (4, Line()),
            (4, LineEffects({Var("<module>", "e"): UNASSIGN}, "error message\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
