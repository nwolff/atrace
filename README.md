# Atrace

[![build status](https://github.com/nwolff/atrace/actions/workflows/test.yml/badge.svg)](https://github.com/nwolff/atrace/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/atrace?color=007ec4&logo=pypi)](https://pypi.org/project/atrace/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/nwolff/atrace)

Automatically prints a trace table of **simple programs**

This module is intended for beginner programmers.

The trace table of [examples/small.py](examples/small.py) is:

```
╭──────┬───┬───┬──────────────┬──────────────┬─────────────────┬─────────╮
│ line │ x │ y │ greet        │ (greet) name │ (greet) message │  output │
├──────┼───┼───┼──────────────┼──────────────┼─────────────────┼─────────┤
│    3 │ 1 │ 3 │              │              │                 │         │
│    6 │ 2 │   │              │              │                 │         │
│    6 │ 3 │   │              │              │                 │         │
│    8 │   │   │              │              │                 │    x: 3 │
│   11 │   │   │ greet("Bob") │        "Bob" │                 │         │
│   12 │   │   │ │            │              │       "Hi Bob!" │         │
│   13 │   │   │ └─ "Hi Bob!" │              │                 │         │
│   16 │   │   │              │              │                 │ Hi Bob! │
╰──────┴───┴───┴──────────────┴──────────────┴─────────────────┴─────────╯
```

## Installing the package

The package is available on pypi.

Install the latest version with uv, pip, the Thonny package manager, etc.

## Generating a trace for code under development

Just import the module at the top of your file, like
in [examples/small.py](examples/small.py#L1)

```
import atrace 

x, y = 1, 3
...
```

Every time you run the program the trace table will be printed when the program exits.

The trace is printed even if the program is interrupted or an uncaught exception is
raised.

Programs that use `input` to interact with the user work, the trace is only printed
at the end of the execution.

## Running as a tool

You can display the trace and other visualizations for existing programs (no
need to `import atrace` in the program).

Note: If you are using `uv` replace the `python3` at the beginning with `uv run`

To display the trace:

    python3 -m atrace examples/fizzbuzz.py

To save the trace to an svg file:

    python3 -m atrace examples/fizzbuzz.py --svg local/fizzbuzz.svg

To display a line-by-line animation of the trace:

    python3 -m atrace.animated examples/fibonacci.py

To display a histogram of how many times each line in a program is executed:
(svg output works the same as for the trace)

    python3 -m atrace.histogram examples/nested_loops.py

To display a line-by-line animation of the histogram:

    python3 -m atrace.animated_histogram examples/fizzbuzz.py 

To display the program with line numbers and syntax highlighting:
(svg output also works here)

    python3 -m atrace.code examples/fizzbuzz.py 

## Compatibility

Requires python version 3.10 or higher.

Tested with:

- cpython
- pypy
- Thonny (with the cpython backend)

## Does not work well with

- Multithreaded programs
- Multi-module programs
- Debuggers
- Classes
- Context managers
