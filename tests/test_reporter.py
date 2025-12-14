import textwrap
import unittest

from atrace.analyzer import Var
from atrace.reporter import history_to_table
from atrace.tracer import Loc


class TestReporter(unittest.TestCase):
    def test_without_output(self):
        history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 0}, ""),
            (Loc("<module>", 5), {Var("<module>", "x"): 1}, ""),
            (Loc("<module>", 5), {Var("<module>", "x"): 2}, ""),
        ]
        expected_table = """\
            ┌────────┬─────┐
            │   line │   x │
            ├────────┼─────┤
            │      3 │   0 │
            │      5 │   1 │
            │      5 │   2 │
            └────────┴─────┘"""
        self.assertEqual(textwrap.dedent(expected_table), history_to_table(history))

    def test_with_output(self):
        history = [
            (Loc("<module>", 3), {Var("<module>", "x"): 1}, ""),
            (Loc("<module>", 4), {}, "1\n"),
        ]
        expected_table = """\
            ┌────────┬─────┬──────────┐
            │   line │ x   │ output   │
            ├────────┼─────┼──────────┤
            │      3 │ 1   │          │
            │      4 │     │ 1        │
            └────────┴─────┴──────────┘"""
        self.assertEqual(textwrap.dedent(expected_table), history_to_table(history))

    def test_with_scopes(self):
        history = [
            (Loc("double", 4), {Var("double", "a"): 3}, ""),
            (Loc("double", 5), {Var("double", "result"): 6}, ""),
            (Loc("<module>", 9), {Var("<module>", "x"): 6}, ""),
        ]
        expected_table = """\
            ┌────────┬──────────────┬───────────────────┬─────┐
            │   line │ (double) a   │ (double) result   │ x   │
            ├────────┼──────────────┼───────────────────┼─────┤
            │      4 │ 3            │                   │     │
            │      5 │              │ 6                 │     │
            │      9 │              │                   │ 6   │
            └────────┴──────────────┴───────────────────┴─────┘"""
        self.assertEqual(textwrap.dedent(expected_table), history_to_table(history))
