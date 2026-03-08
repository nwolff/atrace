import textwrap
import unittest
from unittest import mock

from rich.console import Console

from atrace import UNASSIGN, Call, History, Line, Raise, Return, Var
from atrace.reporter import history_to_table, history_to_table_data


def capture_report(history: History) -> str:
    table = history_to_table(history)
    console = Console(color_system=None)
    with console.capture() as capture:
        console.print(table)
    return capture.get()


class TestReporterTableData(unittest.TestCase):
    def test_assign_none_unassign(self):
        history: History = [
            (1, Line({Var("<module>", "x"): 1}, None)),
            (2, Line({Var("<module>", "x"): None}, None)),
            (3, Line({Var("<module>", "x"): UNASSIGN}, None)),
            (4, Line({Var("<module>", "x"): "bob"}, None)),
        ]
        expected_table_data = (
            ["line", "x"],
            [
                ["1", "1"],
                ["2", "None"],
                ["3", None],
                ["4", '"bob"'],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_assign_then_print(self):
        history: History = [
            (1, Line({Var("<module>", "x"): 1}, None)),
            (2, Line({}, "1\n")),
        ]
        expected_table_data = (
            ["line", "x", "output"],
            [
                ["1", "1", None],
                ["2", None, "1"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_function(self):
        history: History = [
            # We need to pass a callable, otherwise it gets displayed
            (1, Line({Var("<module>", "double"): lambda: None}, None)),
            (6, Line({}, None)),
            (1, Call("double", {Var("double", "a"): 3})),
            (2, Line({Var("double", "result"): 6}, None)),
            (3, Line({}, None)),
            (3, Return(6)),
            (6, Line({Var("<module>", "x"): 6}, None)),
        ]
        expected_table_data = (
            ["line", "(double) a", "(double) result", "x"],
            [
                ["1", "3", None, None],
                ["2", None, "6", None],
                ["6", None, None, "6"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_function_print_before_call(self):
        history: History = [
            # We need to pass a callable, otherwise it gets displayed
            (1, Line({Var("<module>", "double"): lambda: None}, None)),
            (5, Line({}, "hahaha\n")),
            (6, Line({}, None)),
            (1, Call("double", {Var("double", "a"): 5})),
            (2, Line({}, None)),
            (2, Return(10)),
            (6, Line({Var("<module>", "x"): 10}, None)),
        ]
        expected_table_data = (
            ["line", "(double) a", "x", "output"],
            [
                ["5", None, None, "hahaha"],
                ["1", "5", None, None],
                ["6", None, "10", None],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_uncaught_exception(self):
        the_exception = Exception("an exception")
        history: History = [
            (1, Line({}, "hai\n")),
            (2, Line({Var("<module>", "x"): 1}, None)),
            (3, Line({}, None)),
            (3, Raise(type(the_exception), the_exception, mock.ANY)),
        ]
        expected_table_data = (
            ["line", "x", "output", "exception"],
            [
                ["1", None, "hai", None],
                ["2", "1", None, None],
                ["3", None, None, "Exception('an exception')"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))


class TestReporterDisplay(unittest.TestCase):
    def test_small(self):
        history: History = [
            (3, Line({Var("<module>", "x"): 1, Var("<module>", "y"): 3}, None)),
            (5, Line({}, None)),
            (6, Line({Var("<module>", "x"): 2}, None)),
            (5, Line({}, None)),
            (6, Line({Var("<module>", "x"): 3}, None)),
            (5, Line({}, None)),
            (8, Line({}, "x: 3\n")),
            (10, Line({Var("<module>", "t"): (1, "a")}, None)),
            # We need to pass a callable, otherwise it gets displayed
            (13, Line({Var("<module>", "greet"): lambda: None}, None)),
            (18, Line({}, None)),
            (13, Call("greet", {Var("greet", "name"): "Bob"})),
            (14, Line({Var("greet", "message"): "Hello Bob!"}, None)),
            (15, Line({}, None)),
            (15, Return("Hello Bob!")),
            (18, Line({}, "Hello Bob!\n")),
        ]
        expected_result = """\
        ╭───────┬────┬────┬───────────┬───────────────┬──────────────────┬─────────────╮
        │  line │  x │  y │         t │  (greet) name │  (greet) message │      output │
        ├───────┼────┼────┼───────────┼───────────────┼──────────────────┼─────────────┤
        │     3 │  1 │  3 │           │               │                  │             │
        │     6 │  2 │    │           │               │                  │             │
        │     6 │  3 │    │           │               │                  │             │
        │     8 │    │    │           │               │                  │        x: 3 │
        │    10 │    │    │  (1, "a") │               │                  │             │
        │    13 │    │    │           │         "Bob" │                  │             │
        │    14 │    │    │           │               │     "Hello Bob!" │             │
        │    18 │    │    │           │               │                  │  Hello Bob! │
        ╰───────┴────┴────┴───────────┴───────────────┴──────────────────┴─────────────╯
        """
        self.assertEqual(textwrap.dedent(expected_result), capture_report(history))
