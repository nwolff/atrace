# Usage

Automatically prints a trace table of a program once the execution is finished.

Just import the module.

An animated example of a trace table: https://www.101computing.net/using-trace-tables/

An idea of how things look:

```
+-----------+-----+-----+---------+---------------+-----------------------+-------------------------+
|    ligne  |   x |   y | (f) a   | (f) b         | (f) c                 |  affichage              |
+===========+=====+=====+=========+===============+=======================+=========================+
|         5 |   1 |   3 |         |               |                       |                         |
|         7 |   2 |     |         |               |                       |                         |
|         5 |     |   2 |         |               |                       |                         |
|         7 |   3 |     |         |               |                       |                         |
|         5 |     |   1 |         |               |                       |                         |
|         7 |   4 |     |         |               |                       |                         |
|         5 |     |     |         |               |                       |                         |
|         9 |     |     |         |               |                       | somme:  4               |
|        12 |     |     | Bonjour | tout le monde |                       |                         |
|        14 |     |     |         |               | Bonjour tout le monde | Bonjour tout le monde ! |
+-----------+-----+-----+---------+---------------+-----------------------+-------------------------+
```

Does not work with :

- Multithreaded programs
- Multi-module programs
- Classes

# TODO

- Fix line numbers in trace_vars. https://discuss.python.org/t/trace-a-line-after-the-line-but-not-only-before-the-line/89475/7
  This might not even be possible. Start solving it without functions in the scope.
- Then verify things work well in tight loops, for instance the small example
- Thonny, which adds a lot of indirection and magic. Try and find a way to edit the package directly when running in thonny

# Later

- mypy, unit-tests. Integrate in build pipeline
- localize the names of the line and output columns in the report

# Possible enhancements

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
- Parallel assignations show up properly

# Build

Automatically deployed to pypi every time a new tag is pushed: https://pypi.org/project/atrace/

# Inspiration

https://github.com/DarshanLakshman/PyTracerTool/blob/master/PyTracerTool/pytracertool.py

Does almost everything I want, but has many flaws:

- it chokes trying to deepcopy some objects
- it cannot be simply imported into a module
- it fumbles the handling of output (preventing programs with input from working properly).
- it repeats values for no good reason
- its line numbers are very confused
