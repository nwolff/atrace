from dataclasses import dataclass
from typing import Any, TypeAlias


@dataclass(frozen=True)
class PrintEvent:
    text: str


@dataclass(frozen=True)
class Variable:
    scope: str
    name: str


@dataclass(frozen=True)
class ReturnEvent:
    function_name: str
    return_value: Any


@dataclass(frozen=True)
class VariableChangeEvent:
    variable: Variable
    value: Any


@dataclass(frozen=True)
class TraceItem:
    line_no: int
    function_name: str
    event: PrintEvent | VariableChangeEvent | ReturnEvent


Trace: TypeAlias = list[TraceItem]
