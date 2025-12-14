# Usage

Automatically prints a trace table of a program once the execution is finished.

Just import the module.

An animated example of a trace table: https://www.101computing.net/using-trace-tables/

# Requirements/TODO

- Entering a function, binding the local arguments, returning
- Should not interfere with the running program (apart from capturing stdout)
- Should display the trace at the end of execution (not while the program is interacting with the user)
- Should display the trace even if an exception interrupts the program
- Should display the trace even if the user interrupts the program
- Should handle mutations to objects like lists
- Thonny, which adds a shitload of indirection and magic

# Not in scope

- Multithreaded programs
- Multimodule programs
- classes

# Implementation

To capture stdout :

- Either https://docs.python.org/3/library/contextlib.html#contextlib.redirect_stdout
- Or just reassign stdout

To trap sigint:

- https://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python

# Build

Automatically deployed to pypi every time a new tag is pushed: https://pypi.org/project/atrace/

# Technical Refs

- First similar thing I found, doesn't work (chokes on deep copying some variables): https://github.com/DarshanLakshman/PyTracerTool

- 11 years old, doesn't work: https://github.com/mihneadb/python-execution-trace

- A hot mess: https://stackoverflow.com/questions/1645028/trace-table-for-python-programs

- A tutorial on the trace module: https://pymotw.com/2/trace/
