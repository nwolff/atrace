## Usage

Automatically prints a trace table of **simple programs** once the execution is finished.

Just import the module:

```
import atrace  # noqa

x, y = 1, 3

...
```

For instance running test/programs/small_example.py will print:

```
┌────────┬─────┬─────┬────────┬─────────────┬───────────────────┬──────────────┐
│   line │ x   │ y   │ t      │ (greet) n   │ (greet) message   │ output       │
├────────┼─────┼─────┼────────┼─────────────┼───────────────────┼──────────────┤
│      3 │ 1   │ 3   │        │             │                   │              │
│      6 │ 2   │     │        │             │                   │              │
│      6 │ 3   │     │        │             │                   │              │
│      8 │     │     │        │             │                   │ x: 3         │
│     10 │     │     │ (1, 2) │             │                   │              │
│     13 │     │     │        │ bob         │                   │              │
│     14 │     │     │        │             │ bonjour bob!      │              │
│     18 │     │     │        │             │                   │ bonjour bob! │
└────────┴─────┴─────┴────────┴─────────────┴───────────────────┴──────────────┘

```

## Does not work well with

- Multithreaded programs
- Multi-module programs
- Debuggers
- Classes
- Variables containing functions
- Context managers
- Generators
