from dataclasses import dataclass
from typing import Any, TypeAlias


@dataclass
class PrintEvent:
    text: str


@dataclass(frozen=True)
class Variable:
    function_name: str | None
    name: str


@dataclass(frozen=True)
class VariableChangeEvent:
    variable: Variable
    value: Any


@dataclass
class TraceItem:
    line_no: int
    function_name: str
    event: PrintEvent | VariableChangeEvent


Trace: TypeAlias = list[TraceItem]
