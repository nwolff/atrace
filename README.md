# Usage

Automatically prints a trace table of a program once the execution is finished.

Just import the module.

An idea of how things look:

```

```

Does not work with :

- Multithreaded programs
- Multi-module programs
- Classes

# TODO

- Unit tests for the capture part (because the line numbers are so hard). If pytest adds too much magic, then revert to UnitTest
- Fix line numbers in trace_vars. https://discuss.python.org/t/trace-a-line-after-the-line-but-not-only-before-the-line/89475/7
  This might not even be possible. Start solving it without functions in the scope.

- Handle returns (with and without return statements)

- Thonny, which adds a lot of indirection and magic. Try and find a way to edit the package directly when running in thonny

# Later

- localize the names of the line and output columns in the report

# Done

- Sets the program print to stdout unhindered (this is important for input to work properly),
  but captures the prints at the same time to show in the trace at the end.
- Emits the trace at the end if the application ends normally and abruptly (exception, signal, etc.)
- Shows bindings to local variables when entering a function
- Handles mutations to objects like lists (by copying the previous version and then comparing)
- Parallel assignations show up properly
- Changes to variables in other scopes (for instance global)

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
