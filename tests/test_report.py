import pytest

from atrace.model import (
    PrintEvent,
    ReturnEvent,
    TraceItem,
    Variable,
    VariableChangeEvent,
)
from atrace.report import Instant, trace_to_instants


def test_simple_assignments():
    trace = [
        TraceItem(
            line_no=1,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "x"), 1),
        ),
        TraceItem(
            line_no=2,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "y"), 2),
        ),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={Variable("<module>", "x"): 1},
            output="",
        ),
        Instant(
            line_no=2,
            variable_changes={Variable("<module>", "y"): 2},
            output="",
        ),
    ]


def test_parallel_assignments():
    trace = [
        TraceItem(
            line_no=1,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "x"), 1),
        ),
        TraceItem(
            line_no=1,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "y"), 2),
        ),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={
                Variable("<module>", "x"): 1,
                Variable("<module>", "y"): 2,
            },
            output="",
        )
    ]


def test_assignments_in_tight_loop():
    trace = [
        TraceItem(
            line_no=1,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "x"), 1),
        ),
        TraceItem(
            line_no=1,
            function_name="<module>",
            event=VariableChangeEvent(Variable("<module>", "x"), 2),
        ),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={Variable("<module>", "x"): 1},
            output="",
        ),
        Instant(
            line_no=1,
            variable_changes={Variable("<module>", "x"): 2},
            output="",
        ),
    ]


def test_simple_output():
    trace = [
        TraceItem(line_no=1, function_name="<module>", event=PrintEvent("hello")),
        TraceItem(line_no=2, function_name="<module>", event=PrintEvent("world")),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={},
            output="hello",
        ),
        Instant(
            line_no=2,
            variable_changes={},
            output="world",
        ),
    ]


def test_coalesce_output():
    trace = [
        TraceItem(line_no=1, function_name="<module>", event=PrintEvent("hello")),
        TraceItem(line_no=1, function_name="<module>", event=PrintEvent("world")),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={},
            output="helloworld",
        ),
    ]


@pytest.mark.skip(reason="no way of currently testing this")
def test_return_value():
    trace = [
        TraceItem(
            line_no=1,
            function_name="f",
            event=VariableChangeEvent(Variable("f", "x"), 1),
        ),
        TraceItem(
            line_no=2,
            function_name="f",
            event=ReturnEvent("f>", "a return value"),
        ),
    ]

    assert trace_to_instants(trace) == [
        Instant(
            line_no=1,
            variable_changes={Variable("f", "x"): 1},
            output="",
        ),
    ]
