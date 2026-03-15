import textwrap
import unittest
from unittest import mock

from rich.console import Console
from rich.table import Table

from atrace import UNASSIGN, Call, History, Line, LineEffects, Raise, Return, Var
from atrace.reporter import LeftAligned, history_to_table, history_to_table_data


def capture_report(table: Table) -> str:
    console = Console(color_system=None, width=88)
    with console.capture() as capture:
        console.print(table)
    return capture.get()


class TestReporter(unittest.TestCase):
    def test_assign_none_unassign(self):
        history: History = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (2, Line()),
            (2, LineEffects({Var("<module>", "x"): None}, None)),
            (3, Line()),
            (3, LineEffects({Var("<module>", "x"): UNASSIGN}, None)),
            (4, Line()),
            (4, LineEffects({Var("<module>", "x"): "bob"}, None)),
        ]
        expected_table_data = (
            ["line", "x"],
            [
                ["1", "1"],
                ["2", "None"],
                ["3", "✖"],
                ["4", '"bob"'],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_assign_then_print(self):
        history: History = [
            (1, Line()),
            (1, LineEffects({Var("<module>", "x"): 1}, None)),
            (2, Line()),
            (2, LineEffects({}, "1\n")),
        ]
        expected_table_data = (
            ["line", "x", "output"],
            [
                ["1", "1", ""],
                ["2", "", "1"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_function(self):
        history: History = [
            (1, Line()),
            # We need to pass a callable, otherwise it gets displayed
            (1, LineEffects({Var("<module>", "double"): lambda: None}, None)),
            (6, Line()),
            (1, Call("double", {Var("double", "a"): 3})),
            (2, Line()),
            (2, LineEffects({Var("double", "result"): 6}, None)),
            (3, Line()),
            (3, Return(6)),
            (6, LineEffects({Var("<module>", "x"): 6}, None)),
        ]
        expected_table_data = (
            ["line", LeftAligned("double"), "(double) a", "(double) result", "x"],
            [
                ["1", "double(3)", "3", "", ""],
                ["2", "│  ", "", "6", ""],
                ["3", "└─ 6", "", "", ""],
                ["6", "", "", "", "6"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_function_print_before_call(self):
        """This verifies that events happening after we initiated a call get
        assigned to the line we get to after the return"""
        history: History = [
            (1, Line()),
            # We need to pass a callable, otherwise it gets displayed
            (1, LineEffects({Var("<module>", "double"): lambda: None}, None)),
            (5, Line()),
            (5, LineEffects({}, "hahaha\n")),
            (6, Line()),
            (1, Call("double", {Var("double", "a"): 5})),
            (2, Line()),
            (2, Return(10)),
            (6, LineEffects({Var("<module>", "x"): 10}, None)),
        ]
        expected_table_data = (
            ["line", LeftAligned("double"), "(double) a", "x", "output"],
            [
                ["5", "", "", "", "hahaha"],
                ["1", "double(5)", "5", "", ""],
                ["2", "└─ 10", "", "", ""],
                ["6", "", "", "10", ""],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_procedure(self):
        """A function that takes and returns nothing."""
        history: History = [
            (1, Line()),
            # We need to pass a callable, otherwise it gets displayed
            (1, LineEffects({Var("<module>", "p"): lambda: None}, None)),
            (5, Line()),
            (1, Call("p", {})),
            (2, Line()),
            (2, LineEffects({}, "hello\n")),
            (2, Return(None)),
        ]
        expected_table_data = (
            ["line", LeftAligned("p"), "output"],
            [
                ["1", "p()", ""],
                ["2", "│  ", "hello"],
                ["2", "└─ ", ""],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_uncaught_exception(self):
        the_exception = Exception("an exception")
        history: History = [
            (1, Line()),
            (1, LineEffects({}, "hai\n")),
            (2, Line()),
            (2, LineEffects({Var("<module>", "x"): 1}, None)),
            (3, Line()),
            (3, Raise(type(the_exception), the_exception, mock.ANY)),
        ]
        expected_table_data = (
            ["line", "x", "output", "exception"],
            [
                ["1", "", "hai", ""],
                ["2", "1", "", ""],
                ["3", "", "", "Exception('an exception')"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_display(self):
        history: History = [
            (1, Line()),
            (3, Line()),
            (3, LineEffects({Var("<module>", "x"): 1, Var("<module>", "y"): 3}, None)),
            (5, Line()),
            (6, Line()),
            (6, LineEffects({Var("<module>", "x"): 2}, None)),
            (5, Line()),
            (6, Line()),
            (6, LineEffects({Var("<module>", "x"): 3}, None)),
            (5, Line()),
            (8, Line()),
            (8, LineEffects({}, "x: 3\n")),
            (11, Line()),
            # We need to pass a callable, otherwise it gets displayed
            (11, LineEffects({Var("<module>", "greet"): lambda: None}, None)),
            (16, Line()),
            (11, Call("greet", {Var("greet", "name"): "Bob"})),
            (12, Line()),
            (12, LineEffects({Var("greet", "message"): "Hi Bob!"}, None)),
            (13, Line()),
            (13, Return("Hi Bob!")),
            (16, LineEffects({}, "Hi Bob!\n")),
        ]
        expected_result = """\
        ╭──────┬───┬───┬──────────────┬──────────────┬─────────────────┬─────────╮
        │ line │ x │ y │ greet        │ (greet) name │ (greet) message │  output │
        ├──────┼───┼───┼──────────────┼──────────────┼─────────────────┼─────────┤
        │    3 │ 1 │ 3 │              │              │                 │         │
        │    6 │ 2 │   │              │              │                 │         │
        │    6 │ 3 │   │              │              │                 │         │
        │    8 │   │   │              │              │                 │    x: 3 │
        │   11 │   │   │ greet("Bob") │        "Bob" │                 │         │
        │   12 │   │   │ │            │              │       "Hi Bob!" │         │
        │   13 │   │   │ └─ "Hi Bob!" │              │                 │         │
        │   16 │   │   │              │              │                 │ Hi Bob! │
        ╰──────┴───┴───┴──────────────┴──────────────┴─────────────────┴─────────╯
        """
        self.assertEqual(
            textwrap.dedent(expected_result), capture_report(history_to_table(history))
        )
