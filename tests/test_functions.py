import unittest
from unittest import mock

from atrace import (
    Call,
    Line,
    LineEffects,
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

    def test_procedure(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import procedure  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (5, TLine({"p": mock.ANY}, {})),
            (1, TCall({"p": mock.ANY}, {}, "p")),
            (2, TLine({"p": mock.ANY}, {})),
            (2, TOutput("hello\n")),
            (2, TReturn({"p": mock.ANY}, {}, None)),
            (5, TReturn({"p": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "p"): mock.ANY}, None)),
            (5, Line()),
            (1, Call("p", {})),
            (2, Line()),
            (2, LineEffects({}, "hello\n")),
            (2, Return(None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (6, TLine({"double": mock.ANY}, {})),
            (1, TCall({"double": mock.ANY}, {"a": 3}, "double")),
            (2, TLine({"double": mock.ANY}, {"a": 3})),
            (3, TLine({"double": mock.ANY}, {"a": 3, "result": 6})),
            (3, TReturn({"double": mock.ANY}, {"a": 3, "result": 6}, 6)),
            (6, TReturn({"double": mock.ANY, "x": 6}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "double"): mock.ANY}, None)),
            (6, Line()),
            (1, Call("double", {Var("double", "a"): 3})),
            (2, Line()),
            (2, LineEffects({Var("double", "result"): 6}, None)),
            (3, Line()),
            (3, Return(6)),
            (6, LineEffects({Var("<module>", "x"): 6}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_assign_before_call(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_assign_before_call  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (5, TLine({"double": mock.ANY}, {})),
            (6, TLine({"double": mock.ANY, "x": 3}, {})),
            (1, TCall({"double": mock.ANY, "x": 3}, {"a": 5}, "double")),
            (2, TLine({"double": mock.ANY, "x": 3}, {"a": 5})),
            (2, TReturn({"double": mock.ANY, "x": 3}, {"a": 5}, 10)),
            (6, TReturn({"double": mock.ANY, "x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "double"): mock.ANY}, None)),
            (5, Line()),
            (5, LineEffects({Var("<module>", "x"): 3}, None)),
            (6, Line()),
            (1, Call("double", {Var("double", "a"): 5})),
            (2, Line()),
            (2, Return(10)),
            (6, LineEffects({Var("<module>", "x"): 10}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_print_before_call(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_print_before_call  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (5, TLine({"double": mock.ANY}, {})),
            (5, TOutput("hahaha\n")),
            (6, TLine({"double": mock.ANY}, {})),
            (1, TCall({"double": mock.ANY}, {"a": 5}, "double")),
            (2, TLine({"double": mock.ANY}, {"a": 5})),
            (2, TReturn({"double": mock.ANY}, {"a": 5}, 10)),
            (6, TReturn({"double": mock.ANY, "x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "double"): mock.ANY}, None)),
            (5, Line()),
            (5, LineEffects({}, "hahaha\n")),
            (6, Line()),
            (1, Call("double", {Var("double", "a"): 5})),
            (2, Line()),
            (2, Return(10)),
            (6, LineEffects({Var("<module>", "x"): 10}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_modifying_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_modifying_global  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({"c": "start"}, {})),
            (10, TLine({"c": "start", "f": mock.ANY}, {})),
            (4, TCall({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, "f")),
            (6, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (7, TLine({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14})),
            (7, TReturn({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14}, 17)),
            (10, TReturn({"c": 17, "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "c"): "start"}, None)),
            (4, Line()),
            (4, LineEffects({Var("<module>", "f"): mock.ANY}, None)),
            (10, Line()),
            (4, Call("f", {Var("f", "a"): 3, Var("f", "b"): 14})),
            (6, Line()),
            (6, LineEffects({Var("<module>", "c"): 17}, None)),
            (7, Line()),
            (7, Return(17)),
            (10, LineEffects({Var("<module>", "x"): 34}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_shadowing_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_shadowing_global  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (4, TLine({"c": "start"}, {})),
            (9, TLine({"c": "start", "f": mock.ANY}, {})),
            (4, TCall({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, "f")),
            (5, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (6, TLine({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17})),
            (6, TReturn({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}, 17)),
            (9, TReturn({"c": "start", "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "c"): "start"}, None)),
            (4, Line()),
            (4, LineEffects({Var("<module>", "f"): mock.ANY}, None)),
            (9, Line()),
            (4, Call("f", {Var("f", "a"): 3, Var("f", "b"): 14})),
            (5, Line()),
            (5, LineEffects({Var("f", "c"): 17}, None)),
            (6, Line()),
            (6, Return(17)),
            (9, LineEffects({Var("<module>", "x"): 34}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_recursion(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_with_recursion  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (5, TLine({"sum_up_to": mock.ANY}, {})),
            (1, TCall({"sum_up_to": mock.ANY}, {"x": 2}, "sum_up_to")),
            (2, TLine({"sum_up_to": mock.ANY}, {"x": 2})),
            (1, TCall({"sum_up_to": mock.ANY}, {"x": 1}, "sum_up_to")),
            (2, TLine({"sum_up_to": mock.ANY}, {"x": 1})),
            (1, TCall({"sum_up_to": mock.ANY}, {"x": 0}, "sum_up_to")),
            (2, TLine({"sum_up_to": mock.ANY}, {"x": 0})),
            (2, TReturn({"sum_up_to": mock.ANY}, {"x": 0}, 0)),
            (2, TReturn({"sum_up_to": mock.ANY}, {"x": 1}, 1)),
            (2, TReturn({"sum_up_to": mock.ANY}, {"x": 2}, 3)),
            (
                5,
                TReturn({"sum_up_to": mock.ANY, "result": 3}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "sum_up_to"): mock.ANY}, None)),
            (5, Line()),
            (1, Call("sum_up_to", {Var("sum_up_to", "x"): 2})),
            (2, Line()),
            (1, Call("sum_up_to", {Var("sum_up_to", "x"): 1})),
            (2, Line()),
            (1, Call("sum_up_to", {Var("sum_up_to", "x"): 0})),
            (2, Line()),
            (2, Return(0)),
            (2, Return(1)),
            (2, Return(3)),
            (5, LineEffects({Var("<module>", "result"): 3}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_nested_functions(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_nested  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (11, TLine({"outer": mock.ANY}, {})),
            (1, TCall({"outer": mock.ANY}, {"x": 4}, "outer")),
            (2, TLine({"outer": mock.ANY}, {"x": 4})),
            (4, TLine({"outer": mock.ANY}, {"x": 4, "y": 5})),
            (
                8,
                TLine({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}),
            ),
            (4, TCall({"outer": mock.ANY}, {"a": 8, "y": 5}, "inner")),
            (5, TLine({"outer": mock.ANY}, {"a": 8, "y": 5})),
            (6, TLine({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5})),
            (
                6,
                TReturn({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5}, 13),
            ),
            (
                8,
                TReturn({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}, 13),
            ),
            (11, TReturn({"outer": mock.ANY, "result": 13}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "outer"): mock.ANY}, None)),
            (11, Line()),
            (1, Call("outer", {Var("outer", "x"): 4})),
            (2, Line()),
            (2, LineEffects({Var("outer", "y"): 5}, None)),
            (4, Line()),
            (4, LineEffects({Var("outer", "inner"): mock.ANY}, None)),
            (8, Line()),
            # Closures in action!
            (4, Call("inner", {Var("inner", "a"): 8, Var("inner", "y"): 5})),
            (5, Line()),
            (5, LineEffects({Var("inner", "x"): 13}, None)),
            (6, Line()),
            (6, Return(13)),
            (8, Return(13)),
            (11, LineEffects({Var("<module>", "result"): 13}, None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_in_variable(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_in_variable  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (5, TLine({"f": mock.ANY}, {})),
            (7, TLine({"f": mock.ANY, "greet": mock.ANY}, {})),
            (1, TCall({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, "f")),
            (2, TLine({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"})),
            (2, TOutput("Hello Mike\n")),
            (
                2,
                TReturn({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, None),
            ),
            (7, TReturn({"f": mock.ANY, "greet": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "f"): mock.ANY}, None)),
            (5, Line()),
            (5, LineEffects({Var("<module>", "greet"): mock.ANY}, None)),
            (7, Line()),
            (1, Call("f", {Var("f", "name"): "Mike"})),
            (2, Line()),
            (2, LineEffects({}, "Hello Mike\n")),
            (2, Return(None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_lambda(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_lambda  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (2, TLine({"add": mock.ANY}, {})),
            (1, TCall({"add": mock.ANY}, {"x": 5, "y": 3}, mock.ANY)),
            (1, TLine({"add": mock.ANY}, {"x": 5, "y": 3})),
            (1, TReturn({"add": mock.ANY}, {"x": 5, "y": 3}, 8)),
            (2, TOutput("8\n")),
            (2, TReturn({"add": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "add"): mock.ANY}, None)),
            (2, Line()),
            (1, Call("<lambda>", {Var("<lambda>", "x"): 5, Var("<lambda>", "y"): 3})),
            (1, Line()),
            (1, Return(8)),
            (2, LineEffects({}, "8\n")),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_generator(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_generator  # noqa

        expected_trace = [
            (0, TCall({}, {}, "<module>")),
            (1, TLine({}, {})),
            (7, TLine({"countdown": mock.ANY}, {})),
            (1, TCall({"countdown": mock.ANY}, {"n": 1}, "countdown")),
            (2, TLine({"countdown": mock.ANY}, {"n": 1})),
            (3, TLine({"countdown": mock.ANY}, {"n": 1})),
            (3, TReturn({"countdown": mock.ANY}, {"n": 1}, 1)),
            (8, TLine({"countdown": mock.ANY, "num": 1}, {})),
            (8, TOutput(text="1\n")),
            (7, TLine({"countdown": mock.ANY, "num": 1}, {})),
            (
                3,
                TCall(
                    {"countdown": mock.ANY, "num": 1},
                    {"n": 1},
                    "countdown",
                ),
            ),
            (4, TLine({"countdown": mock.ANY, "num": 1}, {"n": 1})),
            (2, TLine({"countdown": mock.ANY, "num": 1}, {"n": 0})),
            (
                2,
                TReturn({"countdown": mock.ANY, "num": 1}, {"n": 0}, None),
            ),
            (7, TReturn({"countdown": mock.ANY, "num": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "countdown"): mock.ANY}, None)),
            (7, Line()),
            (1, Call("countdown", {Var("countdown", "n"): 1})),
            (2, Line()),
            (3, Line()),
            (3, Return(1)),
            (7, LineEffects({Var("<module>", "num"): 1}, None)),
            (8, Line()),
            (8, LineEffects({}, "1\n")),
            (7, Line()),
            (3, Call("countdown", {Var("countdown", "n"): 1})),
            (4, Line()),
            (4, LineEffects({Var("countdown", "n"): 0}, None)),
            (2, Line()),
            (2, Return(None)),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
