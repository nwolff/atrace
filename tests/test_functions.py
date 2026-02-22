import unittest
from unittest import mock

import atrace
from atrace.core.analyzer import Filters, Var, trace_to_history
from atrace.core.tracer import Call, Line, Loc, Output, Return


class TestFunctions(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_function(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 9), Line({"double": mock.ANY}, {})),
            (Loc("double", 4), Call({"double": mock.ANY}, {"a": 3})),
            (Loc("double", 5), Line({"double": mock.ANY}, {"a": 3})),
            (Loc("double", 6), Line({"double": mock.ANY}, {"a": 3, "result": 6})),
            (Loc("double", 6), Return({"double": mock.ANY}, {"a": 3, "result": 6}, 6)),
            (Loc("<module>", 9), Return({"double": mock.ANY, "x": 6}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "double"): mock.ANY}, None),
            (Loc("double", 4), {Var("double", "a"): 3}, None),
            (Loc("double", 5), {Var("double", "result"): 6}, None),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

        # See what life looks like when we don't filter

        expected_full_history = [
            (Loc("<module>", 1), {}, None),
            (Loc("<module>", 4), {Var("<module>", "double"): mock.ANY}, None),
            (Loc("double", 4), {Var("double", "a"): 3}, None),
            (Loc("double", 5), {Var("double", "result"): 6}, None),
            (Loc("double", 6), {}, None),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, None),
        ]
        self.assertEqual(
            expected_full_history,
            trace_to_history(self.trace, Filters.NONE),
        )

    def test_function_assign_before_call(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_assign_before_call  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 8), Line({"double": mock.ANY}, {})),
            (Loc("<module>", 9), Line({"double": mock.ANY, "x": 3}, {})),
            (Loc("double", 4), Call({"double": mock.ANY, "x": 3}, {"a": 5})),
            (Loc("double", 5), Line({"double": mock.ANY, "x": 3}, {"a": 5})),
            (Loc("double", 5), Return({"double": mock.ANY, "x": 3}, {"a": 5}, 10)),
            (Loc("<module>", 9), Return({"double": mock.ANY, "x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "double"): mock.ANY}, None),
            (Loc("<module>", 8), {Var("<module>", "x"): 3}, None),
            (Loc("double", 4), {Var("double", "a"): 5}, None),
            (Loc("<module>", 9), {Var("<module>", "x"): 10}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_modifying_global(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_modifying_global  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 6), Line({"c": "start"}, {})),
            (Loc("<module>", 12), Line({"c": "start", "f": mock.ANY}, {})),
            (Loc("f", 6), Call({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (Loc("f", 8), Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (Loc("f", 9), Line({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14})),
            (Loc("f", 9), Return({"c": 17, "f": mock.ANY}, {"a": 3, "b": 14}, 17)),
            (Loc("<module>", 12), Return({"c": 17, "f": mock.ANY, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "c"): "start"}, None),
            (Loc("<module>", 6), {Var("<module>", "f"): mock.ANY}, None),
            (Loc("f", 6), {Var("f", "a"): 3, Var("f", "b"): 14}, None),
            (Loc("f", 8), {Var("<module>", "c"): 17}, None),
            (Loc("<module>", 12), {Var("<module>", "x"): 34}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_shadowing_global(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_shadowing_global  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 3), Line({}, {})),
            (Loc("<module>", 6), Line({"c": "start"}, {})),
            (Loc("<module>", 11), Line({"c": "start", "f": mock.ANY}, {})),
            (Loc("f", 6), Call({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (Loc("f", 7), Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14})),
            (
                Loc("f", 8),
                Line({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}),
            ),
            (
                Loc("f", 8),
                Return({"c": "start", "f": mock.ANY}, {"a": 3, "b": 14, "c": 17}, 17),
            ),
            (
                Loc("<module>", 11),
                Return({"c": "start", "f": mock.ANY, "x": 34}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "c"): "start"}, None),
            (Loc("<module>", 6), {Var("<module>", "f"): mock.ANY}, None),
            (Loc("f", 6), {Var("f", "a"): 3, Var("f", "b"): 14}, None),
            (Loc("f", 7), {Var("f", "c"): 17}, None),
            (Loc("<module>", 11), {Var("<module>", "x"): 34}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_with_recursion(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_with_recursion  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 8), Line({"sum_up_to": mock.ANY}, {})),
            (Loc("sum_up_to", 4), Call({"sum_up_to": mock.ANY}, {"x": 2})),
            (Loc("sum_up_to", 5), Line({"sum_up_to": mock.ANY}, {"x": 2})),
            (Loc("sum_up_to", 4), Call({"sum_up_to": mock.ANY}, {"x": 1})),
            (Loc("sum_up_to", 5), Line({"sum_up_to": mock.ANY}, {"x": 1})),
            (Loc("sum_up_to", 4), Call({"sum_up_to": mock.ANY}, {"x": 0})),
            (Loc("sum_up_to", 5), Line({"sum_up_to": mock.ANY}, {"x": 0})),
            (Loc("sum_up_to", 5), Return({"sum_up_to": mock.ANY}, {"x": 0}, 0)),
            (Loc("sum_up_to", 5), Return({"sum_up_to": mock.ANY}, {"x": 1}, 1)),
            (Loc("sum_up_to", 5), Return({"sum_up_to": mock.ANY}, {"x": 2}, 3)),
            (
                Loc("<module>", 8),
                Return({"sum_up_to": mock.ANY, "result": 3}, {}, None),
            ),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "sum_up_to"): mock.ANY}, None),
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 2}, None),
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 1}, None),
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 0}, None),
            (Loc("<module>", 8), {Var("<module>", "result"): 3}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_nested(self):
        """
        Maybe the surprising thing is that when we access y from inner, y appears in our scope.
        This is how the python runtime works.
        """
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_nested  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 14), Line({"outer": mock.ANY}, {})),
            (Loc("outer", 4), Call({"outer": mock.ANY}, {"x": 4})),
            (Loc("outer", 5), Line({"outer": mock.ANY}, {"x": 4})),
            (Loc("outer", 7), Line({"outer": mock.ANY}, {"x": 4, "y": 5})),
            (
                Loc("outer", 11),
                Line({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}),
            ),
            (Loc("inner", 7), Call({"outer": mock.ANY}, {"a": 8, "y": 5})),
            (Loc("inner", 8), Line({"outer": mock.ANY}, {"a": 8, "y": 5})),
            (Loc("inner", 9), Line({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5})),
            (
                Loc("inner", 9),
                Return({"outer": mock.ANY}, {"a": 8, "x": 13, "y": 5}, 13),
            ),
            (
                Loc("outer", 11),
                Return({"outer": mock.ANY}, {"x": 4, "y": 5, "inner": mock.ANY}, 13),
            ),
            (Loc("<module>", 14), Return({"outer": mock.ANY, "result": 13}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "outer"): mock.ANY}, None),
            (Loc("outer", 4), {Var("outer", "x"): 4}, None),
            (Loc("outer", 5), {Var("outer", "y"): 5}, None),
            (Loc("outer", 7), {Var("outer", "inner"): mock.ANY}, None),
            (Loc("inner", 7), {Var("inner", "a"): 8, Var("inner", "y"): 5}, None),
            (Loc("inner", 8), {Var("inner", "x"): 13}, None),
            (Loc("<module>", 14), {Var("<module>", "result"): 13}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_in_variable(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_in_variable  # noqa

        expected_trace = [
            (Loc("<module>", 0), Call({}, {})),
            (Loc("<module>", 1), Line({}, {})),
            (Loc("<module>", 4), Line({}, {})),
            (Loc("<module>", 8), Line({"f": mock.ANY}, {})),
            (Loc("<module>", 10), Line({"f": mock.ANY, "greet": mock.ANY}, {})),
            (Loc("f", 4), Call({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"})),
            (Loc("f", 5), Line({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"})),
            (Loc("f", 5), Output("Hello")),
            (Loc("f", 5), Output(" ")),
            (Loc("f", 5), Output("Mike")),
            (Loc("f", 5), Output("\n")),
            (
                Loc("f", 5),
                Return({"f": mock.ANY, "greet": mock.ANY}, {"name": "Mike"}, None),
            ),
            (Loc("<module>", 10), Return({"f": mock.ANY, "greet": mock.ANY}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "f"): mock.ANY}, None),
            (Loc("<module>", 8), {Var("<module>", "greet"): mock.ANY}, None),
            (Loc("f", 4), {Var("f", "name"): "Mike"}, None),
            (Loc("f", 5), {}, "Hello Mike\n"),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )

    def test_function_lambda(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_lambda  # noqa

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "add"): mock.ANY}, None),
            (
                Loc("<lambda>", 3),
                {Var("<lambda>", "y"): 3, Var("<lambda>", "x"): 5},
                None,
            ),
            (Loc("<module>", 4), {}, "8\n"),
        ]
        self.assertEqual(
            expected_history, trace_to_history(self.trace, Filters.NO_EFFECT)
        )

    def test_function_generator(self):
        """
        Kind of works, except one sees one too many variable assignment in the generator
        when we re-enter the generator.
        """
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_generator  # noqa

        expected_history = [
            (Loc("<module>", 4), {Var("<module>", "countdown"): mock.ANY}, None),
            (Loc("countdown", 4), {Var("countdown", "n"): 2}, None),
            (Loc("<module>", 10), {Var("<module>", "num"): 2}, None),
            (Loc("<module>", 11), {}, "2\n"),
            (Loc("countdown", 6), {Var("countdown", "n"): 2}, None),
            (Loc("countdown", 7), {Var("countdown", "n"): 1}, None),
            (Loc("<module>", 10), {Var("<module>", "num"): 1}, None),
            (Loc("<module>", 11), {}, "1\n"),
            (Loc("countdown", 6), {Var("countdown", "n"): 1}, None),
            (Loc("countdown", 7), {Var("countdown", "n"): 0}, None),
        ]
        self.assertEqual(
            expected_history,
            trace_to_history(self.trace, Filters.NO_EFFECT),
        )
