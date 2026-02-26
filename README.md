# Atrace

[![build status](https://github.com/nwolff/atrace/actions/workflows/test.yml/badge.svg)](https://github.com/nwolff/atrace/actions)
[![PyPI - Version](https://img.shields.io/pypi/v/atrace?color=007ec4&logo=pypi)](https://pypi.org/project/atrace/)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/nwolff/atrace)

Automatically prints a trace table of **simple programs**

This module is intended for beginner programmers.

## Usage

Just import the module:

```
import atrace  # noqa

x, y = 1, 3
...
```

For instance running test/programs/small_example.py will print this table at the end:

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
