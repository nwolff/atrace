import unittest
from unittest import mock

from atrace import (
    UNASSIGN,
    Call,
    ExceptionOccurred,
    Line,
    Meta,
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
            (0, Call({}, {}, "<module>")),
            (2, Line({}, {})),
            (4, Line({}, {})),
            (6, Line({"x": 1}, {})),
            (
                6,
                ExceptionOccurred({"x": 1}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (6, Return({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (2, {}, None, Meta.NONE),
            (4, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (6, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_uncaught_exception(self):
        trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .snippets import uncaught_exception  # noqa

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {}, "hai\n", Meta.NONE),
            (4, {Var("<module>", "x"): 1}, None, Meta.NONE),
            (5, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_caught_exception(self):
        trace_next_loaded_module(self.callback_done)

        from .snippets import caught_exception  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({}, {})),
            (
                4,
                ExceptionOccurred({}, {}, mock.ANY, mock.ANY, mock.ANY),
            ),
            (5, Line({}, {})),
            (6, Line({"e": mock.ANY}, {})),
            (6, Output("error message")),
            (6, Output("\n")),
            (6, Return({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {}, None, Meta.NONE),
            (4, {}, None, Meta.NONE),
            (5, {Var("<module>", "e"): mock.ANY}, None, Meta.NONE),
            (
                6,
                {Var("<module>", "e"): UNASSIGN},
                "error message\n",
                Meta.NONE,
            ),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
