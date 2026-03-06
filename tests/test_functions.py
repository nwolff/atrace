import unittest
from unittest import mock

from atrace import (
    Call,
    Line,
    Meta,
    Output,
    Return,
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
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (9, Line({"double": mock.ANY}, {})),
            (4, Call({"double": mock.ANY}, {"a": 3}, function_name="double")),
            (5, Line({"double": mock.ANY}, {"a": 3})),
            (6, Line({"double": mock.ANY}, {"a": 3, "result": 6})),
            (6, Return({"double": mock.ANY}, {"a": 3, "result": 6}, 6)),
            (9, Return({"double": mock.ANY, "x": 6}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (
                4,
                {Var("<module>", "double"): mock.ANY},
                None,
                Meta.NONE,
            ),
            (4, {Var("double", "a"): 3}, None, Meta.CALL),
            (5, {Var("double", "result"): 6}, None, Meta.NONE),
            (6, {}, None, Meta.RETURN),
            (9, {Var("<module>", "x"): 6}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_assign_before_call(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_assign_before_call  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (8, Line({"double": mock.ANY}, {})),
            (9, Line({"double": mock.ANY, "x": 3}, {})),
            (4, Call({"double": mock.ANY, "x": 3}, {"a": 5}, function_name="double")),
            (5, Line({"double": mock.ANY, "x": 3}, {"a": 5})),
            (5, Return({"double": mock.ANY, "x": 3}, {"a": 5}, 10)),
            (9, Return({"double": mock.ANY, "x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (
                4,
                {Var("<module>", "double"): mock.ANY},
                None,
                Meta.NONE,
            ),
            (8, {Var("<module>", "x"): 3}, None, Meta.NONE),
            (4, {Var("double", "a"): 5}, None, Meta.CALL),
            (5, {}, None, Meta.RETURN),
            (9, {Var("<module>", "x"): 10}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_modifying_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_modifying_global  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (6, Line({"c": "start"}, {})),
            (12, Line({"c": "start", "f": mock.ANY}, {})),
            (
                6,
                Call(
                    {"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, function_name="f"
                ),
            ),
            (8, Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (9, Line({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14})),
            (9, Return({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14}, 17)),
            (12, Return({"c": 17, "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "c"): "start"}, None, Meta.NONE),
            (6, {Var("<module>", "f"): mock.ANY}, None, Meta.NONE),
            (6, {Var("f", "a"): 3, Var("f", "b"): 14}, None, Meta.CALL),
            (8, {Var("<module>", "c"): 17}, None, Meta.NONE),
            (9, {}, None, Meta.RETURN),
            (12, {Var("<module>", "x"): 34}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_shadowing_global(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_shadowing_global  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (6, Line({"c": "start"}, {})),
            (11, Line({"c": "start", "f": mock.ANY}, {})),
            (
                6,
                Call(
                    {"c": "start", "f": mock.ANY}, {"a": 3, "b": 14}, function_name="f"
                ),
            ),
            (7, Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (
                8,
                Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}),
            ),
            (
                8,
                Return({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}, 17),
            ),
            (
                11,
                Return({"c": "start", "f": mock.ANY, "x": 34}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "c"): "start"}, None, Meta.NONE),
            (6, {Var("<module>", "f"): mock.ANY}, None, Meta.NONE),
            (6, {Var("f", "a"): 3, Var("f", "b"): 14}, None, Meta.CALL),
            (7, {Var("f", "c"): 17}, None, Meta.NONE),
            (8, {}, None, Meta.RETURN),
            (11, {Var("<module>", "x"): 34}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_with_recursion(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_with_recursion  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (8, Line({"sum_up_to": mock.ANY}, {})),
            (4, Call({"sum_up_to": mock.ANY}, {"x": 2}, function_name="sum_up_to")),
            (5, Line({"sum_up_to": mock.ANY}, {"x": 2})),
            (4, Call({"sum_up_to": mock.ANY}, {"x": 1}, function_name="sum_up_to")),
            (5, Line({"sum_up_to": mock.ANY}, {"x": 1})),
            (4, Call({"sum_up_to": mock.ANY}, {"x": 0}, function_name="sum_up_to")),
            (5, Line({"sum_up_to": mock.ANY}, {"x": 0})),
            (5, Return({"sum_up_to": mock.ANY}, {"x": 0}, 0)),
            (5, Return({"sum_up_to": mock.ANY}, {"x": 1}, 1)),
            (5, Return({"sum_up_to": mock.ANY}, {"x": 2}, 3)),
            (
                8,
                Return({"sum_up_to": mock.ANY, "result": 3}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (
                4,
                {Var("<module>", "sum_up_to"): mock.ANY},
                None,
                Meta.NONE,
            ),
            (4, {Var("sum_up_to", "x"): 2}, None, Meta.CALL),
            (4, {Var("sum_up_to", "x"): 1}, None, Meta.CALL),
            (4, {Var("sum_up_to", "x"): 0}, None, Meta.CALL),
            (5, {}, None, Meta.RETURN),
            (5, {}, None, Meta.RETURN),
            (5, {}, None, Meta.RETURN),
            (8, {Var("<module>", "result"): 3}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_nested(self):
        """
        Maybe the surprising thing is when we access y from inner, y appears in scope.
        This is how the python runtime works.
        """
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_nested  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (14, Line({"outer": mock.ANY}, {})),
            (4, Call({"outer": mock.ANY}, {"x": 4}, function_name="outer")),
            (5, Line({"outer": mock.ANY}, {"x": 4})),
            (7, Line({"outer": mock.ANY}, {"x": 4, "y": 5})),
            (
                11,
                Line({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}),
            ),
            (7, Call({"outer": mock.ANY}, {"a": 8, "y": 5}, function_name="inner")),
            (8, Line({"outer": mock.ANY}, {"a": 8, "y": 5})),
            (9, Line({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5})),
            (
                9,
                Return({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5}, 13),
            ),
            (
                11,
                Return({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}, 13),
            ),
            (14, Return({"outer": mock.ANY, "result": 13}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (4, {Var("<module>", "outer"): mock.ANY}, None, Meta.NONE),
            (4, {Var("outer", "x"): 4}, None, Meta.CALL),
            (5, {Var("outer", "y"): 5}, None, Meta.NONE),
            (7, {Var("outer", "inner"): mock.ANY}, None, Meta.NONE),
            (
                7,
                {Var("inner", "a"): 8, Var("inner", "y"): 5},
                None,
                Meta.CALL,
            ),
            (8, {Var("inner", "x"): 13}, None, Meta.NONE),
            (9, {}, None, Meta.RETURN),
            (11, {}, None, Meta.RETURN),
            (14, {Var("<module>", "result"): 13}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_in_variable(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_in_variable  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (8, Line({"f": mock.ANY}, {})),
            (10, Line({"f": mock.ANY, "greet": mock.ANY}, {})),
            (
                4,
                Call(
                    {"f": mock.ANY, "greet": mock.ANY},
                    {"name": "Mike"},
                    function_name="f",
                ),
            ),
            (5, Line({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"})),
            (5, Output("Hello")),
            (5, Output(" ")),
            (5, Output("Mike")),
            (5, Output("\n")),
            (
                5,
                Return({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, None),
            ),
            (10, Return({"f": mock.ANY, "greet": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (4, {Var("<module>", "f"): mock.ANY}, None, Meta.NONE),
            (8, {Var("<module>", "greet"): mock.ANY}, None, Meta.NONE),
            (4, {Var("f", "name"): "Mike"}, None, Meta.CALL),
            (5, {}, "Hello Mike\n", Meta.RETURN),
            (10, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_lambda(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_lambda  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (3, Line({}, {})),
            (4, Line({"add": mock.ANY}, {})),
            (3, Call({"add": mock.ANY}, {"x": 5, "y": 3}, function_name=mock.ANY)),
            (3, Line({"add": mock.ANY}, {"x": 5, "y": 3})),
            (3, Return({"add": mock.ANY}, {"x": 5, "y": 3}, 8)),
            (4, Output("8")),
            (4, Output("\n")),
            (4, Return({"add": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (3, {Var("<module>", "add"): mock.ANY}, None, Meta.NONE),
            (
                3,
                {Var("<lambda>", "y"): 3, Var("<lambda>", "x"): 5},
                None,
                Meta.CALL,
            ),
            (3, {}, None, Meta.RETURN),
            (4, {}, "8\n", Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_generator(self):
        trace_next_loaded_module(self.callback_done)
        from .snippets import function_generator  # noqa

        expected_trace = [
            (0, Call({}, {}, "<module>")),
            (1, Line({}, {})),
            (4, Line({}, {})),
            (10, Line({"countdown": mock.ANY}, {})),
            (4, Call({"countdown": mock.ANY}, {"n": 1}, function_name="countdown")),
            (5, Line({"countdown": mock.ANY}, {"n": 1})),
            (6, Line({"countdown": mock.ANY}, {"n": 1})),
            (6, Return({"countdown": mock.ANY}, {"n": 1}, 1)),
            (11, Line({"countdown": mock.ANY, "num": 1}, {})),
            (11, Output(text="1")),
            (11, Output(text="\n")),
            (10, Line({"countdown": mock.ANY, "num": 1}, {})),
            (
                6,
                Call(
                    {"countdown": mock.ANY, "num": 1},
                    {"n": 1},
                    function_name="countdown",
                ),
            ),
            (7, Line({"countdown": mock.ANY, "num": 1}, {"n": 1})),
            (5, Line({"countdown": mock.ANY, "num": 1}, {"n": 0})),
            (
                5,
                Return({"countdown": mock.ANY, "num": 1}, {"n": 0}, None),
            ),
            (10, Return({"countdown": mock.ANY, "num": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (1, {}, None, Meta.NONE),
            (
                4,
                {Var("<module>", "countdown"): mock.ANY},
                None,
                Meta.NONE,
            ),
            (4, {Var("countdown", "n"): 1}, None, Meta.CALL),
            (5, {}, None, Meta.NONE),
            (6, {}, None, Meta.RETURN),
            (10, {Var("<module>", "num"): 1}, None, Meta.NONE),
            (11, {}, "1\n", Meta.NONE),
            (6, {Var("countdown", "n"): 1}, None, Meta.CALL),
            (7, {Var("countdown", "n"): 0}, None, Meta.NONE),
            (5, {}, None, Meta.RETURN),
            (10, {}, None, Meta.NONE),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
