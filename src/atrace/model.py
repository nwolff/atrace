from dataclasses import dataclass
from typing import Any, TypeAlias


@dataclass
class PrintEvent:
    text: str


@dataclass
class Variable:
    function_name: str | None
    name: str


@dataclass
class VariableChangeEvent:
    variable: Variable
    value: Any


@dataclass
class TraceItem:
    line_no: int
    function_name: str
    event: PrintEvent | VariableChangeEvent | None


Trace: TypeAlias = list[TraceItem]
