import time
from collections.abc import Callable
from typing import TypeAlias

from rich.console import Console, RenderableType
from rich.live import Live

from . import History

# The extra information we display is always tied to line numbers.

NumberedLines: TypeAlias = list[tuple[int, str]]


def add_line_numbers(source: str) -> NumberedLines:
    return [(i + 1, line) for i, line in enumerate(source.splitlines())]


# Scrolling support


def visible_program_lines(
    numbered_lines: NumberedLines, current_lineno: int | None
) -> NumberedLines:
    display_height = Console().size.height - 1
    if current_lineno:
        start_idx = max(0, current_lineno - display_height)
    else:
        start_idx = 0
    end_idx = min(len(numbered_lines), start_idx + display_height)

    return numbered_lines[start_idx:end_idx]


# Animation support

ANIMATION_SECONDS = 5

GenerateDisplay: TypeAlias = Callable[
    [NumberedLines, History, int | None], RenderableType
]


def animate(
    numbered_lines: NumberedLines, history: History, generate_display: GenerateDisplay
) -> None:

    with Live(None, auto_refresh=False) as live:
        for index in range(len(history)):
            history_up_to_now = history[: index + 1]
            current_lineno, _ = history[index]
            live.update(
                generate_display(numbered_lines, history_up_to_now, current_lineno),
                refresh=True,
            )
            time.sleep(ANIMATION_SECONDS / len(history))
        live.update(
            generate_display(numbered_lines, history, None),
            refresh=True,
        )
