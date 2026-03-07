import textwrap
import unittest
from unittest import mock

from rich.console import Console

from atrace import UNASSIGN, Call, History, Line, Return, Var
from atrace.reporter import history_to_table, history_to_table_data


def capture_report(history: History) -> str:
    table = history_to_table(history)
    console = Console(color_system=None)
    with console.capture() as capture:
        console.print(table)
    return capture.get()


class TestReporter(unittest.TestCase):
    def test_all_assignments(self):
        history: History = [
            (3, Line({Var("<module>", "x"): 1}, None)),
            (4, Line({Var("<module>", "x"): None}, None)),
            (5, Line({Var("<module>", "x"): UNASSIGN}, None)),
            (6, Line({Var("<module>", "x"): "bob"}, None)),
        ]
        expected_table_data = (
            ["line", "x"],
            [
                ["3", "1"],
                ["4", "None"],
                ["5", None],
                ["6", '"bob"'],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_with_output(self):
        history: History = [
            (1, Line({}, None)),
            (3, Line({Var("<module>", "x"): 1}, None)),
            (4, Line({}, "1\n")),
        ]
        expected_table_data = (
            ["line", "x", "output"],
            [["3", "1", None], ["4", None, "1"]],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_with_functions(self):
        history: History = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "double"): mock.ANY}, None)),
            (9, Line({}, None)),
            (4, Call("double", {Var("double", "a"): 3})),
            (5, Line({Var("double", "result"): 6}, None)),
            (6, Return(6)),
            (9, Line({Var("<module>", "x"): 6}, None)),
        ]
        expected_table_data = (
            ["line", "double", "(double) a", "(double) result", "x"],
            [
                ["4", mock.ANY, None, None, None],
                ["4", None, "3", None, None],
                ["5", None, None, "6", None],
                ["9", None, None, None, "6"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_weird(self):
        history: History = [
            (1, Line({}, None)),
            (4, Line({Var("<module>", "double"): mock.ANY}, None)),
            (8, Line({}, "hahaha\n")),
            (9, Line({}, None)),
            (4, Call("double", {Var("double", "a"): 5})),
            (5, Line({}, None)),
            (5, Return(10)),
            (9, Line({Var("<module>", "x"): 10}, None)),
        ]
        expected_table_data = (
            ["line", "double", "(double) a", "x", "output"],
            [
                ["4", "<ANY>", None, None, None],
                ["8", None, None, None, "hahaha"],
                ["4", None, "5", None, None],
                ["5", None, None, None, None],
                ["9", None, None, "10", None],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_display(self):
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
