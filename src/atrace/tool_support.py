import time
from collections.abc import Callable
from typing import TypeAlias

from rich.console import Console, RenderableType
from rich.live import Live

from . import History, Loc

# The extra information we display is always tied to line numbers.

NumberedLines: TypeAlias = list[tuple[int, str]]


def add_line_numbers(source: str) -> NumberedLines:
    return [(i + 1, line) for i, line in enumerate(source.splitlines())]


# Scrolling support

display_height = Console().size.height - 1


def visible_lines(
    numbered_lines: NumberedLines, current_loc: Loc | None
) -> NumberedLines:
    if current_loc:
        start_idx = max(0, current_loc.line_no - display_height)
    else:
        start_idx = 0
    end_idx = min(len(numbered_lines), start_idx + display_height)

    return numbered_lines[start_idx:end_idx]


# Animation support

ANIMATION_SECONDS = 5

GenerateDisplay: TypeAlias = Callable[
    [NumberedLines, History, Loc | None], RenderableType
]


def animate(
    numbered_lines: NumberedLines, history: History, generate_display: GenerateDisplay
) -> None:

    with Live(None, auto_refresh=False) as live:
        for index in range(len(history)):
            history_up_to_now = history[: index + 1]
            current_loc, _, _ = history[index]
            live.update(
                generate_display(numbered_lines, history_up_to_now, current_loc),
                refresh=True,
            )
            time.sleep(ANIMATION_SECONDS / len(history))
        live.update(
            generate_display(numbered_lines, history, None),
            refresh=True,
        )
