import unittest

import atrace
from atrace.analyzer import Var, trace_to_history
from atrace.tracer import CallEvent, LineEvent, Loc, ReturnEvent


class TestFunctions(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_function(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({}, {})),
            (Loc("<module>", 9), LineEvent({}, {})),
            (Loc("double", 4), CallEvent({}, {"a": 3})),
            (Loc("double", 5), LineEvent({}, {"a": 3})),
            (Loc("double", 6), LineEvent({}, {"a": 3, "result": 6})),
            (Loc("double", 6), ReturnEvent({}, {"a": 3, "result": 6}, 6)),
            (Loc("<module>", 9), ReturnEvent({"x": 6}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("double", 4), {Var("double", "a"): 3}, ""),
            (Loc("double", 5), {Var("double", "result"): 6}, ""),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_assign_before_call(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_assign_before_call  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({}, {})),
            (Loc("<module>", 8), LineEvent({}, {})),
            (Loc("<module>", 9), LineEvent({"x": 3}, {})),
            (Loc("double", 4), CallEvent({"x": 3}, {"a": 5})),
            (Loc("double", 5), LineEvent({"x": 3}, {"a": 5})),
            (Loc("double", 5), ReturnEvent({"x": 3}, {"a": 5}, 10)),
            (Loc("<module>", 9), ReturnEvent({"x": 10}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 8), {Var("<module>", "x"): 3}, ""),
            (Loc("double", 4), {Var("double", "a"): 5}, ""),
            (Loc("<module>", 9), {Var("<module>", "x"): 10}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_modifying_global(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_modifying_global  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 6), LineEvent({"c": "start"}, {})),
            (Loc("<module>", 12), LineEvent({"c": "start"}, {})),
            (Loc("f", 6), CallEvent({"c": "start"}, {"a": 3, "b": 14})),
            (Loc("f", 8), LineEvent({"c": "start"}, {"a": 3, "b": 14})),
            (Loc("f", 9), LineEvent({"c": 17}, {"a": 3, "b": 14})),
            (Loc("f", 9), ReturnEvent({"c": 17}, {"a": 3, "b": 14}, 17)),
            (Loc("<module>", 12), ReturnEvent({"c": 17, "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "c"): "start"}, ""),
            (Loc("f", 6), {Var("f", "a"): 3, Var("f", "b"): 14}, ""),
            (Loc("f", 8), {Var("<module>", "c"): 17}, ""),
            (Loc("<module>", 12), {Var("<module>", "x"): 34}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_shadowing_global(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_shadowing_global  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 6), LineEvent({"c": "start"}, {})),
            (Loc("<module>", 11), LineEvent({"c": "start"}, {})),
            (Loc("f", 6), CallEvent({"c": "start"}, {"a": 3, "b": 14})),
            (Loc("f", 7), LineEvent({"c": "start"}, {"a": 3, "b": 14})),
            (Loc("f", 8), LineEvent({"c": "start"}, {"a": 3, "b": 14, "c": 17})),
            (Loc("f", 8), ReturnEvent({"c": "start"}, {"a": 3, "b": 14, "c": 17}, 17)),
            (Loc("<module>", 11), ReturnEvent({"c": "start", "x": 34}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)
        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "c"): "start"}, ""),
            (Loc("f", 6), {Var("f", "a"): 3, Var("f", "b"): 14}, ""),
            (Loc("f", 7), {Var("f", "c"): 17}, ""),
            (Loc("<module>", 11), {Var("<module>", "x"): 34}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_nested(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_nested  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({}, {})),
            (Loc("<module>", 14), LineEvent({}, {})),
            (Loc("outer", 4), CallEvent({}, {"x": 4})),
            (Loc("outer", 5), LineEvent({}, {"x": 4})),
            (Loc("outer", 7), LineEvent({}, {"x": 4, "y": 5})),
            (Loc("outer", 11), LineEvent({}, {"x": 4, "y": 5})),
            (Loc("inner", 7), CallEvent({}, {"a": 8, "y": 5})),
            (Loc("inner", 8), LineEvent({}, {"a": 8, "y": 5})),
            (Loc("inner", 9), LineEvent({}, {"a": 8, "x": 13, "y": 5})),
            (Loc("inner", 9), ReturnEvent({}, {"a": 8, "x": 13, "y": 5}, 13)),
            (Loc("outer", 11), ReturnEvent({}, {"x": 4, "y": 5}, 13)),
            (Loc("<module>", 14), ReturnEvent({"result": 13}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("outer", 4), {Var("outer", "x"): 4}, ""),
            (Loc("outer", 5), {Var("outer", "y"): 5}, ""),
            (Loc("inner", 7), {Var("inner", "a"): 8, Var("inner", "y"): 5}, ""),
            (Loc("inner", 8), {Var("inner", "x"): 13}, ""),
            (Loc("<module>", 14), {Var("<module>", "result"): 13}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_function_with_recursion(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import function_with_recursion  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({}, {})),
            (Loc("<module>", 8), LineEvent({}, {})),
            (Loc("sum_up_to", 4), CallEvent({}, {"x": 2})),
            (Loc("sum_up_to", 5), LineEvent({}, {"x": 2})),
            (Loc("sum_up_to", 4), CallEvent({}, {"x": 1})),
            (Loc("sum_up_to", 5), LineEvent({}, {"x": 1})),
            (Loc("sum_up_to", 4), CallEvent({}, {"x": 0})),
            (Loc("sum_up_to", 5), LineEvent({}, {"x": 0})),
            (Loc("sum_up_to", 5), ReturnEvent({}, {"x": 0}, 0)),
            (Loc("sum_up_to", 5), ReturnEvent({}, {"x": 1}, 1)),
            (Loc("sum_up_to", 5), ReturnEvent({}, {"x": 2}, 3)),
            (Loc("<module>", 8), ReturnEvent({"result": 3}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 2}, ""),
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 1}, ""),
            (Loc("sum_up_to", 4), {Var("sum_up_to", "x"): 0}, ""),
            (Loc("<module>", 8), {Var("<module>", "result"): 3}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
