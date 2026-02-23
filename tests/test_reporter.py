import textwrap
import unittest
from unittest import mock

from rich.console import Console

from atrace import UNASSIGN, History, Loc, Var
from atrace.reporter import history_to_table, history_to_table_data


def capture_report(history: History) -> str:
    table = history_to_table(history)
    console = Console(color_system=None)
    with console.capture() as capture:
        console.print(table)
    return capture.get()


class TestReporterFromHistory(unittest.TestCase):
    def test_all_assignments(self):
        history: History = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {Var("<module>", "x"): None}, None),
            (Loc("<module>", 5), {Var("<module>", "x"): UNASSIGN}, None),
            (Loc("<module>", 6), {Var("<module>", "x"): 2}, None),
        ]
        expected_table_data = (
            ["line", "x"],
            [
                ["3", "1"],
                ["4", "None"],
                ["5", None],
                ["6", "2"],
            ],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_with_output(self):
        history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {}, "1\n"),
        ]
        expected_table_data = (
            ["line", "x", "output"],
            [["3", "1", None], ["4", None, "1"]],
        )
        self.assertEqual(expected_table_data, history_to_table_data(history))

    def test_with_functions(self):
        history: History = [
            (Loc("<module>", 4), {Var("<module>", "double"): mock.ANY}, None),
            (Loc("double", 4), {Var("double", "a"): 3}, None),
            (Loc("double", 5), {Var("double", "result"): 6}, None),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, None),
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

    def test_display(self):
        history: History = [
            (
                Loc("<module>", 3),
                {Var("<module>", "x"): 1, Var("<module>", "y"): 3},
                None,
            ),
            (Loc("<module>", 6), {Var("<module>", "x"): 2}, None),
            (Loc("<module>", 6), {Var("<module>", "x"): 3}, None),
            (Loc("<module>", 8), {}, "x: 3\n"),
            (Loc("<module>", 10), {Var("<module>", "t"): (1, 2)}, None),
            (Loc("greet", 13), {Var("greet", "name"): "Bob"}, None),
            (Loc("greet", 14), {Var("greet", "message"): "Hello Bob!"}, None),
            (Loc("<module>", 18), {}, "Hello Bob!\n"),
        ]
        expected_result = """\
        ╭───────┬────┬────┬─────────┬───────────────┬──────────────────┬─────────────╮
        │  line │  x │  y │       t │  (greet) name │  (greet) message │      output │
        ├───────┼────┼────┼─────────┼───────────────┼──────────────────┼─────────────┤
        │     3 │  1 │  3 │         │               │                  │             │
        │     6 │  2 │    │         │               │                  │             │
        │     6 │  3 │    │         │               │                  │             │
        │     8 │    │    │         │               │                  │        x: 3 │
        │    10 │    │    │  (1, 2) │               │                  │             │
        │    13 │    │    │         │           Bob │                  │             │
        │    14 │    │    │         │               │       Hello Bob! │             │
        │    18 │    │    │         │               │                  │  Hello Bob! │
        ╰───────┴────┴────┴─────────┴───────────────┴──────────────────┴─────────────╯
        """
        self.assertEqual(textwrap.dedent(expected_result), capture_report(history))
