import textwrap
import unittest

from atrace.analyzer import UNASSIGN, Var
from atrace.reporter import history_to_report, history_to_table
from atrace.tracer import Loc


class TestReporterTables(unittest.TestCase):
    def test_all_assignments(self):
        history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {Var("<module>", "x"): None}, None),
            (Loc("<module>", 5), {Var("<module>", "x"): UNASSIGN}, None),
            (Loc("<module>", 6), {Var("<module>", "x"): 2}, None),
        ]
        expected_table = [
            {"line": 3, "x": 1},
            {"line": 4, "x": "None"},
            {"line": 5, "x": None},
            {"line": 6, "x": 2},
        ]
        self.assertEqual(expected_table, history_to_table(history))

    def test_with_output(self):
        history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, None),
            (Loc("<module>", 4), {}, "1\n"),
        ]
        expected_table = [
            {"line": 3, "x": 1, "output": None},
            {"line": 4, "x": None, "output": "1\n"},
        ]
        self.assertEqual(expected_table, history_to_table(history))

    def test_with_scopes(self):
        history = [
            (Loc("double", 4), {Var("double", "a"): 3}, None),
            (Loc("double", 5), {Var("double", "result"): 6}, None),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, None),
        ]
        expected_table = [
            {"line": 4, "(double) a": 3, "(double) result": None, "x": None},
            {"line": 5, "(double) a": None, "(double) result": 6, "x": None},
            {"line": 9, "(double) a": None, "(double) result": None, "x": 6},
        ]
        self.assertEqual(expected_table, history_to_table(history))


class TestReporterFinalResult(unittest.TestCase):
    def test_reporter_final_result(self):
        history = [
            (
                Loc("<module>", 3),
                {Var("<module>", "x"): 1, Var("<module>", "y"): 3},
                None,
            ),
            (Loc("<module>", 6), {Var("<module>", "x"): 2}, None),
            (Loc("<module>", 6), {Var("<module>", "x"): 3}, None),
            (Loc("<module>", 8), {}, "x: 3\n"),
            (Loc("<module>", 10), {Var("<module>", "t"): (1, 2)}, None),
            (Loc("greet", 13), {Var("greet", "n"): "bob"}, None),
            (Loc("greet", 14), {Var("greet", "message"): "bonjour bob!"}, None),
            (Loc("<module>", 18), {}, "bonjour bob!\n"),
        ]
        expected_result = """\
        ╭────────┬─────┬─────┬────────┬─────────────┬───────────────────┬──────────────╮
        │   line │   x │   y │ t      │ (greet) n   │ (greet) message   │ output       │
        ├────────┼─────┼─────┼────────┼─────────────┼───────────────────┼──────────────┤
        │      3 │   1 │   3 │        │             │                   │              │
        │      6 │   2 │     │        │             │                   │              │
        │      6 │   3 │     │        │             │                   │              │
        │      8 │     │     │        │             │                   │ x: 3         │
        │     10 │     │     │ (1, 2) │             │                   │              │
        │     13 │     │     │        │ bob         │                   │              │
        │     14 │     │     │        │             │ bonjour bob!      │              │
        │     18 │     │     │        │             │                   │ bonjour bob! │
        ╰────────┴─────┴─────┴────────┴─────────────┴───────────────────┴──────────────╯"""
        self.assertEqual(textwrap.dedent(expected_result), history_to_report(history))
