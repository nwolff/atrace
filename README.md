# TODO:

- entering a function, binding the local arguments, returning
- ignore function definitions (look at the type of object)

- display at end only

# Usage and intent

A package that automatically prints a trace table of a program, just by importing the module

- Should not interfere with the running program (apart from capturing stdout)
- Should display the trace at the end of execution (not while the program is interacting with the user)
- Should display the trace even if an exception interrupts the program
- Should display the trace even if the user interrupts the program
- Should handle mutations to objects like lists
- Should handle functions properly:
  - entering the function
  - binding the local arguments
  - returning

An animated example of a trace table: https://www.101computing.net/using-trace-tables/

# Not in scope

- Multithreaded programs

# Implementation

To trace variables :

- Either https://docs.python.org/3/library/sys.html#sys.settrace
- Or https://docs.python.org/3/library/trace.html

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
