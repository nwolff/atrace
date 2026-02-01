# Usage

Automatically prints a trace table of a program once the execution is finished.

Just import the module.

An animated example of a trace table: https://www.101computing.net/using-trace-tables/

An idea of how things look:

```
+--------+-------------+-------------+----------------------------+-----------+-----------+----------+
|   Line | (double)a   | (double)b   | (main)l                    | (main)x   | (main)y   | OUTPUT   |
+========+=============+=============+============================+===========+===========+==========+
|      2 |             |             |                            | 0         |           |          |
+--------+-------------+-------------+----------------------------+-----------+-----------+----------+
|      3 |             |             |                            | 0         | 10        |          |
+--------+-------------+-------------+----------------------------+-----------+-----------+----------+
|      5 |             |             |                            | 0         | 10        |    10    |
+--------+-------------+-------------+----------------------------+-----------+-----------+----------+
```

Does not work with :

- Multithreaded programs
- Multi-module programs

# TODO

- Build the goddam table
- Fix line numbers in trace_vars
- Parallel assignations show up properly
- Thonny, which adds a lot of indirection and magic

# Later

- Make robust. In other words should never raise an exception. ruff check, mypy, unit-tests.
- Handle classes better
- More details when recursive invocations
- Think about how to show returns
- Find if there could be a good use for colors in the trace

# Done

- Sets the program print to stdout unhindered (this is important for input to work properly),
  but captures the prints at the same time to show in the trace at the end.
- Emits the trace at the end if the application ends normally and abruptly (exception, signal, etc.)
- Shows bindings to local variables when entering a function
- Handles mutations to objects like lists (by copying the previous version and then comparing)

# Build

Automatically deployed to pypi every time a new tag is pushed: https://pypi.org/project/atrace/

# Inspiration

https://github.com/DarshanLakshman/PyTracerTool/blob/master/PyTracerTool/pytracertool.py

Does almost everything I want, but has many flaws:

- it chokes trying to deepcopy some objects
- it cannot be simply imported into a module
- it fumbles the handling of output (preventing programs with input from working properly).
