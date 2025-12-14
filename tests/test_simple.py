import unittest
from unittest import mock

import atrace
from atrace.analyzer import Var, trace_to_history
from atrace.tracer import CallEvent, LineEvent, Loc, OutputEvent, ReturnEvent


class TestSimple(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_assignment(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import assignment  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 3), ReturnEvent({"x": 1}, {}, None)),
        ]

        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_parallel_assignment(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import parallel_assignment  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 3), ReturnEvent({"x": 1, "y": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (
                Loc("<module>", 3),
                {Var("<module>", "x"): 1, Var("<module>", "y"): 2},
                "",
            ),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_print(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import print as _print  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 3), OutputEvent("hello")),
            (Loc("<module>", 3), OutputEvent("\n")),
            (Loc("<module>", 3), ReturnEvent({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {}, "hello\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_assign_then_print(self):
        atrace.trace_next_loaded_module(self.callback_done)
        from .programs import assign_then_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({"x": 1}, {})),
            (Loc("<module>", 4), OutputEvent("1")),
            (Loc("<module>", 4), OutputEvent("\n")),
            (Loc("<module>", 4), ReturnEvent({"x": 1}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, ""),
            (Loc("<module>", 4), {}, "1\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_input(self):
        atrace.trace_next_loaded_module(self.callback_done)
        mock.builtins.input = lambda _: "Bob"

        from .programs import input  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({"x": "Bob"}, {})),
            (Loc("<module>", 4), OutputEvent("hello")),
            (Loc("<module>", 4), OutputEvent(" ")),
            (Loc("<module>", 4), OutputEvent("Bob")),
            (Loc("<module>", 4), OutputEvent("\n")),
            (Loc("<module>", 4), ReturnEvent({"x": "Bob"}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): "Bob"}, ""),
            (Loc("<module>", 4), {}, "hello Bob\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_while_loop(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import while_loop  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({"x": 0}, {})),
            (Loc("<module>", 5), LineEvent({"x": 0}, {})),
            (Loc("<module>", 4), LineEvent({"x": 1}, {})),
            (Loc("<module>", 5), LineEvent({"x": 1}, {})),
            (Loc("<module>", 4), LineEvent({"x": 2}, {})),
            (Loc("<module>", 4), ReturnEvent({"x": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 0}, ""),
            (Loc("<module>", 5), {Var("<module>", "x"): 1}, ""),
            (Loc("<module>", 5), {Var("<module>", "x"): 2}, ""),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_for_with_print(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import for_with_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({"i": 0}, {})),
            (Loc("<module>", 4), OutputEvent("0")),
            (Loc("<module>", 4), OutputEvent("\n")),
            (Loc("<module>", 3), LineEvent({"i": 0}, {})),
            (Loc("<module>", 4), LineEvent({"i": 1}, {})),
            (Loc("<module>", 4), OutputEvent("1")),
            (Loc("<module>", 4), OutputEvent("\n")),
            (Loc("<module>", 3), LineEvent({"i": 1}, {})),
            (Loc("<module>", 4), LineEvent({"i": 2}, {})),
            (Loc("<module>", 4), OutputEvent("2")),
            (Loc("<module>", 4), OutputEvent("\n")),
            (Loc("<module>", 3), LineEvent({"i": 2}, {})),
            (Loc("<module>", 3), ReturnEvent({"i": 2}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "i"): 0}, ""),
            (Loc("<module>", 4), {}, "0\n"),
            (Loc("<module>", 3), {Var("<module>", "i"): 1}, ""),
            (Loc("<module>", 4), {}, "1\n"),
            (Loc("<module>", 3), {Var("<module>", "i"): 2}, ""),
            (Loc("<module>", 4), {}, "2\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_loop_with_mutation_and_print(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import loop_with_mutation_and_print  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({"lst": ["a", "b"]}, {})),
            (Loc("<module>", 5), LineEvent({"lst": ["a", "b"]}, {})),
            (Loc("<module>", 5), OutputEvent("a")),
            (Loc("<module>", 5), OutputEvent("\n")),
            (Loc("<module>", 4), LineEvent({"lst": ["b"]}, {})),
            (Loc("<module>", 5), LineEvent({"lst": ["b"]}, {})),
            (Loc("<module>", 5), OutputEvent("b")),
            (Loc("<module>", 5), OutputEvent("\n")),
            (Loc("<module>", 4), LineEvent({"lst": []}, {})),
            (Loc("<module>", 4), ReturnEvent({"lst": []}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 3), {Var("<module>", "lst"): ["a", "b"]}, ""),
            (Loc("<module>", 5), {Var("<module>", "lst"): ["b"]}, "a\n"),
            (Loc("<module>", 5), {Var("<module>", "lst"): []}, "b\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_nothing(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import nothing  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 1), ReturnEvent({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = []
        self.assertEqual(expected_history, trace_to_history(self.trace))

    def test_import(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import importing  # noqa

        expected_trace = [
            (Loc("<module>", 0), CallEvent({}, {})),
            (Loc("<module>", 1), LineEvent({}, {})),
            (Loc("<module>", 3), LineEvent({}, {})),
            (Loc("<module>", 4), LineEvent({}, {})),
            (Loc("<module>", 6), LineEvent({}, {})),
            (Loc("<module>", 6), OutputEvent("3.141592653589793")),
            (Loc("<module>", 6), OutputEvent("\n")),
            (Loc("<module>", 6), ReturnEvent({}, {}, None)),
        ]
        self.assertEqual(expected_trace, self.trace)

        expected_history = [
            (Loc("<module>", 6), {}, "3.141592653589793\n"),
        ]
        self.assertEqual(expected_history, trace_to_history(self.trace))
