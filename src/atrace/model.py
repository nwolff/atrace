from dataclasses import dataclass


@dataclass
class PrintEvent:
    line: int
    text: str
