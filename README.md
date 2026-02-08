# Usage

Automatically prints a trace table of a program once the execution is finished.

Just import the module.

An idea of how things look (this is the trace of tests/programs/small.py):

```
┌─────────┬─────┬─────┬────────┬─────────────┬───────────────────┬──────────────┐
│   ligne │ x   │ y   │ t      │ (greet) n   │ (greet) message   │ affichage     │
├─────────┼─────┼─────┼────────┼─────────────┼───────────────────┼──────────────┤
│       3 │ 1   │ 3   │        │             │                   │              │
│       6 │ 2   │     │        │             │                   │              │
│       6 │ 3   │     │        │             │                   │              │
│       8 │     │     │        │             │                   │ x: 3         │
│      10 │     │     │ (1, 2) │             │                   │              │
│      13 │     │     │        │ bob         │                   │              │
│      14 │     │     │        │             │ bonjour bob!      │              │
│      18 │     │     │        │             │                   │ bonjour bob! │
└─────────┴─────┴─────┴────────┴─────────────┴───────────────────┴──────────────┘
```

Does not work with :

- Multithreaded programs
- Multi-module programs
- Classes

# Done

- Sets the program print to stdout unhindered (this is important for input to work properly),
  but captures the prints at the same time to show in the trace at the end.
- Emits the trace at the end if the application ends normally and abruptly (exception, signal, etc.)
- Shows bindings to local variables when entering a function
- Handles mutations to objects like lists (by copying the previous version and then comparing)
- Parallel assignations show up properly
- Changes to variables in other scopes (for instance global)
