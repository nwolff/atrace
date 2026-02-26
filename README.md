# Atrace

[![build status](https://github.com/nwolff/atrace/actions/workflows/test.yml/badge.svg)](https://github.com/nwolff/atrace/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/atrace?color=007ec4&logo=pypi)](https://pypi.org/project/atrace/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/nwolff/atrace)

Automatically prints a trace table of **simple programs**

This module is intended for beginner programmers.

The trace table of test/programs/small_example.py is:

```
╭───────┬────┬────┬─────────┬───────────────┬──────────────────┬─────────────╮
│  line │  x │  y │       t │  (greet) name │  (greet) message │      output │
├───────┼────┼────┼─────────┼───────────────┼──────────────────┼─────────────┤
│     3 │  1 │  3 │         │               │                  │             │
│     6 │  2 │    │         │               │                  │             │
│     6 │  3 │    │         │               │                  │             │
│     8 │    │    │         │               │                  │        x: 3 │
│    10 │    │    │  (1, 2) │               │                  │             │
│    13 │    │    │         │           Bob │                  │             │
│    14 │    │    │         │               │       Hello Bob! │             │
│    18 │    │    │         │               │                  │  Hello Bob! │
╰───────┴────┴────┴─────────┴───────────────┴──────────────────┴─────────────╯
```

## Generating a trace for code under development

Just import the module at the top of your file:

```
import atrace  # noqa

x, y = 1, 3
...
```

Every time you run the program the trace table will be printed when the program exits.
The trace is printed even if the program is interrupted or an uncaught exception is
raised.

## Generating different views and animations of the program run

You don't need to import atrace in the programs if you run the tool like this.

To display the trace for a program :

    uv run -m atrace tests/programs/small_example.py

To display a histogram of how many times lines are executed in a program :

    uv run -m atrace.histogram tests/programs/histogram_example.py

To display a line by line animation of the histogram :

    uv run -m atrace.animated_histogram tests/programs/fizzbuzz_example.py 

## Compatibility

Requires python version 3.10 or higher.

Tested with:

- cpython
- pypy
- Thonny

## Does not work well with

- Multithreaded programs
- Multi-module programs
- Debuggers
- Classes
- Variables containing functions
- Context managers
- Generators
