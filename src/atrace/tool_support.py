import contextlib
import io
import time
from collections.abc import Callable, Iterator
from typing import NamedTuple, TypeAlias

from rich.console import Console, RenderableType
from rich.live import Live

from . import History

# The extra information we display is always tied to line numbers.
NumberedLines: TypeAlias = list[tuple[int, str]]


def add_line_numbers(source: str) -> NumberedLines:
    return [(i + 1, line) for i, line in enumerate(source.splitlines())]


@contextlib.contextmanager
def terminal_or_svg(svg_path: str | None) -> Iterator[Console]:
    """Provides a Rich Console context that either prints to the terminal
    or captures output to an SVG file.

    If svg_path is provided, stdout is redirected to an internal buffer,
    recording the output and saving it as an SVG upon exiting the context.
    If svg_path is None, it yields a standard live-printing Console.

    Args:
        svg_path (str | None): The file path to save the SVG. If None,
                               output defaults to the standard terminal.

    Yields:
        rich.console.Console: A console instance configured for the chosen mode.
    """
    if svg_path is not None:
        # Create a console that records but doesn't print to the terminal
        # We use a dummy file (io.StringIO) to suppress stdout
        capture_console = Console(record=True, file=io.StringIO(), width=120)
        yield capture_console
        capture_console.save_svg(svg_path, title="Python Trace")
        print(f"Successfully saved trace to {svg_path}")
    else:
        yield Console()


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


class Context(NamedTuple):
    numbered_lines: NumberedLines
    history: History
    current_lineno: int | None = None


GenerateDisplay: TypeAlias = Callable[[Context], RenderableType]


def animate(
    numbered_lines: NumberedLines, history: History, generate_display: GenerateDisplay
) -> None:

    with Live(None, auto_refresh=False) as live:
        for index in range(len(history)):
            history_up_to_now = history[: index + 1]
            current_lineno, _ = history[index]
            live.update(
                generate_display(
                    Context(numbered_lines, history_up_to_now, current_lineno)
                ),
                refresh=True,
            )
            time.sleep(ANIMATION_SECONDS / len(history))

        # Final frame without any line highlighted
        live.update(
            generate_display(Context(numbered_lines, history_up_to_now)),
            refresh=True,
        )
