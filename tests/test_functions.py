import unittest
from unittest import mock

from atrace import (
    Call,
    Line,
    Return,
    TCall,
    TLine,
    TOutput,
    TReturn,
    Var,
    trace_next_loaded_module,
    trace_to_history,
)


class TestFunctions(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_function(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (9, TLine({"double": mock.ANY}, {})),
            (4, TCall({"double": mock.ANY}, {"a": 3}, "double")),
            (5, TLine({"double": mock.ANY}, {"a": 3})),
            (6, TLine({"double": mock.ANY}, {"a": 3, "result": 6})),
            (6, TReturn({"double": mock.ANY}, {"a": 3, "result": 6}, 6)),
            (9, TReturn({"double": mock.ANY, "x": 6}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "double"): mock.ANY}, None)),
            (9, Line({}, None)),
            (4, Call("double", {Var("double", "a"): 3})),
            (5, Line({Var("double", "result"): 6}, None)),
            (6, Line({}, None)),
            (6, Return(6)),
            (9, Line({Var("<module>", "x"): 6}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_assign_before_call(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_assign_before_call  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (8, TLine({"double": mock.ANY}, {})),
            (9, TLine({"double": mock.ANY, "x": 3}, {})),
            (4, TCall({"double": mock.ANY, "x": 3}, {"a": 5}, "double")),
            (5, TLine({"double": mock.ANY, "x": 3}, {"a": 5})),
            (5, TReturn({"double": mock.ANY, "x": 3}, {"a": 5}, 10)),
            (9, TReturn({"double": mock.ANY, "x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "double"): mock.ANY}, None)),
            (8, Line({Var("<module>", "x"): 3}, None)),
            (9, Line({}, None)),
            (4, Call("double", {Var("double", "a"): 5})),
            (5, Line({}, None)),
            (5, Return(10)),
            (9, Line({Var("<module>", "x"): 10}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_modifying_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_modifying_global  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (6, TLine({"c": "start"}, {})),
            (12, TLine({"c": "start", "f": mock.ANY}, {})),
            (6, TCall({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, "f")),
            (8, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (9, TLine({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14})),
            (9, TReturn({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14}, 17)),
            (12, TReturn({"c": 17, "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "c"): "start"}, None)),
            (6, Line({Var("<module>", "f"): mock.ANY}, None)),
            (12, Line({}, None)),
            (6, Call("f", {Var("f", "a"): 3, Var("f", "b"): 14})),
            (8, Line({Var("<module>", "c"): 17}, None)),
            (9, Line({}, None)),
            (9, Return(17)),
            (12, Line({Var("<module>", "x"): 34}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_shadowing_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_shadowing_global  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (6, TLine({"c": "start"}, {})),
            (11, TLine({"c": "start", "f": mock.ANY}, {})),
            (6, TCall({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, "f")),
            (7, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (8, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17})),
            (8, TReturn({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}, 17)),
            (11, TReturn({"c": "start", "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "c"): "start"}, None)),
            (6, Line({Var("<module>", "f"): mock.ANY}, None)),
            (11, Line({}, None)),
            (6, Call("f", {Var("f", "a"): 3, Var("f", "b"): 14})),
            (7, Line({Var("f", "c"): 17}, None)),
            (8, Line({}, None)),
            (8, Return(17)),
            (11, Line({Var("<module>", "x"): 34}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_with_recursion(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_with_recursion  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (8, TLine({"sum_up_to": mock.ANY}, {})),
            (4, TCall({"sum_up_to": mock.ANY}, {"x": 2}, "sum_up_to")),
            (5, TLine({"sum_up_to": mock.ANY}, {"x": 2})),
            (4, TCall({"sum_up_to": mock.ANY}, {"x": 1}, "sum_up_to")),
            (5, TLine({"sum_up_to": mock.ANY}, {"x": 1})),
            (4, TCall({"sum_up_to": mock.ANY}, {"x": 0}, "sum_up_to")),
            (5, TLine({"sum_up_to": mock.ANY}, {"x": 0})),
            (5, TReturn({"sum_up_to": mock.ANY}, {"x": 0}, 0)),
            (5, TReturn({"sum_up_to": mock.ANY}, {"x": 1}, 1)),
            (5, TReturn({"sum_up_to": mock.ANY}, {"x": 2}, 3)),
            (
                8,
                TReturn({"sum_up_to": mock.ANY, "result": 3}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "sum_up_to"): mock.ANY}, None)),
            (8, Line({}, None)),
            (4, Call("sum_up_to", {Var("sum_up_to", "x"): 2})),
            (5, Line({}, None)),
            (4, Call("sum_up_to", {Var("sum_up_to", "x"): 1})),
            (5, Line({}, None)),
            (4, Call("sum_up_to", {Var("sum_up_to", "x"): 0})),
            (5, Line({}, None)),
            (5, Return(0)),
            (5, Return(1)),
            (5, Return(3)),
            (8, Line({Var("<module>", "result"): 3}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_nested(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_nested  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (14, TLine({"outer": mock.ANY}, {})),
            (4, TCall({"outer": mock.ANY}, {"x": 4}, "outer")),
            (5, TLine({"outer": mock.ANY}, {"x": 4})),
            (7, TLine({"outer": mock.ANY}, {"x": 4, "y": 5})),
            (
                11,
                TLine({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}),
            ),
            (7, TCall({"outer": mock.ANY}, {"a": 8, "y": 5}, "inner")),
            (8, TLine({"outer": mock.ANY}, {"a": 8, "y": 5})),
            (9, TLine({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5})),
            (
                9,
                TReturn({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5}, 13),
            ),
            (
                11,
                TReturn({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}, 13),
            ),
            (14, TReturn({"outer": mock.ANY, "result": 13}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "outer"): mock.ANY}, None)),
            (14, Line({}, None)),
            (4, Call("outer", {Var("outer", "x"): 4})),
            (5, Line({Var("outer", "y"): 5}, None)),
            (7, Line({Var("outer", "inner"): mock.ANY}, None)),
            (11, Line({}, None)),
            # Closures in action!
            (7, Call("inner", {Var("inner", "a"): 8, Var("inner", "y"): 5})),
            (8, Line({Var("inner", "x"): 13}, None)),
            (9, Line({}, None)),
            (9, Return(13)),
            (11, Return(13)),
            (14, Line({Var("<module>", "result"): 13}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_in_variable(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_in_variable  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (8, TLine({"f": mock.ANY}, {})),
            (10, TLine({"f": mock.ANY, "greet": mock.ANY}, {})),
            (4, TCall({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, "f")),
            (5, TLine({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"})),
            (5, TOutput("Hello Mike\n")),
            (
                5,
                TReturn({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, None),
            ),
            (10, TReturn({"f": mock.ANY, "greet": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "f"): mock.ANY}, None)),
            (8, Line({Var("<module>", "greet"): mock.ANY}, None)),
            (10, Line({}, None)),
            (4, Call("f", {Var("f", "name"): "Mike"})),
            (5, Line({}, "Hello Mike\n")),
            (5, Return(None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_lambda(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_lambda  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (3, TLine({}, {})),
            (4, TLine({"add": mock.ANY}, {})),
            (3, TCall({"add": mock.ANY}, {"x": 5, "y": 3}, mock.ANY)),
            (3, TLine({"add": mock.ANY}, {"x": 5, "y": 3})),
            (3, TReturn({"add": mock.ANY}, {"x": 5, "y": 3}, 8)),
            (4, TOutput("8\n")),
            (4, TReturn({"add": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "add"): mock.ANY}, None)),
            (4, Line({}, None)),
            (3, Call("<lambda>", {Var("<lambda>", "x"): 5, Var("<lambda>", "y"): 3})),
            (3, Line({}, None)),
            (3, Return(8)),
            (4, Line({}, "8\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_generator(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_generator  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({}, {})),
            (10, TLine({"countdown": mock.ANY}, {})),
            (4, TCall({"countdown": mock.ANY}, {"n": 1}, "countdown")),
            (5, TLine({"countdown": mock.ANY}, {"n": 1})),
            (6, TLine({"countdown": mock.ANY}, {"n": 1})),
            (6, TReturn({"countdown": mock.ANY}, {"n": 1}, 1)),
            (11, TLine({"countdown": mock.ANY, "num": 1}, {})),
            (11, TOutput(text="1\n")),
            (10, TLine({"countdown": mock.ANY, "num": 1}, {})),
            (
                6,
                TCall(
                    {"countdown": mock.ANY, "num": 1},
                    {"n": 1},
                    "countdown",
                ),
            ),
            (7, TLine({"countdown": mock.ANY, "num": 1}, {"n": 1})),
            (5, TLine({"countdown": mock.ANY, "num": 1}, {"n": 0})),
            (
                5,
                TReturn({"countdown": mock.ANY, "num": 1}, {"n": 0}, None),
            ),
            (10, TReturn({"countdown": mock.ANY, "num": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "countdown"): mock.ANY}, None)),
            (10, Line({}, None)),
            (4, Call("countdown", {Var("countdown", "n"): 1})),
            (5, Line({}, None)),
            (6, Line({}, None)),
            (6, Return(1)),
            (10, Line({Var("<module>", "num"): 1}, None)),
            (11, Line({}, "1\n")),
            (10, Line({}, None)),
            (6, Call("countdown", {Var("countdown", "n"): 1})),
            (7, Line({Var("countdown", "n"): 0}, None)),
            (5, Line({}, None)),
            (5, Return(None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
