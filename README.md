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

# Requirements/TODO

- Think of how to show function activation / scopes / variables that are deleted (that last one is easy, just stop showing it). Some good ideas in pytracetool

- Entering a function, binding the local arguments, returning
- Should display the trace even if an exception interrupts the program
- Should display the trace even if the user interrupts the program
- Use colors in the trace ?
- Thonny, which adds a shitload of indirection and magic
- unit tests
- Make robust. In other words should never raise an exception.

# Later

- Replace sys.\_getframe with public api calls (unless too slow) ?

# Done

- lets the program print to stdout unhindered, but captures the prints at the same time, to show in the trace at the end
- Emits the trace at the end if the application ends normally.
- Handles mutations to objects like lists (by copying the previous version and then comparing)

# Not in scope

- Multithreaded programs
- Multimodule programs
- classes

# Build

Automatically deployed to pypi every time a new tag is pushed: https://pypi.org/project/atrace/

# Refs

- https://docs.python.org/3/library/sys.html#sys.settrace The python doc for settrace

- https://stackoverflow.com/questions/16258553/how-can-i-define-algebraic-data-types-in-python To model the events in the trace

- https://stackoverflow.com/questions/23468042/the-invocation-of-signal-handler-and-atexit-handler-in-python to dump the trace when the program stops, no matter how.

# Technical Refs

- https://github.com/DarshanLakshman/PyTracerTool Does almost everything I want, but has two flaws: it chokes trying to deepcopy some objects, it cannot be simply imported into a module.

- https://github.com/mihneadb/python-execution-trace 11 years old, doesn't work at all

- https://stackoverflow.com/questions/1645028/trace-table-for-python-programs Some ideas in there
