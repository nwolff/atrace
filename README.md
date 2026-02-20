# Atrace

![build status](https://github.com/nwolff/atrace/actions/workflows/test.yml/badge.svg)

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
╭────────┬─────┬─────┬────────┬─────────────┬───────────────────┬──────────────╮
│   line │   x │   y │ t      │ (greet) n   │ (greet) message   │ output       │
├────────┼─────┼─────┼────────┼─────────────┼───────────────────┼──────────────┤
│      3 │   1 │   3 │        │             │                   │              │
│      6 │   2 │     │        │             │                   │              │
│      6 │   3 │     │        │             │                   │              │
│      8 │     │     │        │             │                   │ x: 3         │
│     10 │     │     │ (1, 2) │             │                   │              │
│     13 │     │     │        │ bob         │                   │              │
│     14 │     │     │        │             │ bonjour bob!      │              │
│     18 │     │     │        │             │                   │ bonjour bob! │
╰────────┴─────┴─────┴────────┴─────────────┴───────────────────┴──────────────╯
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
