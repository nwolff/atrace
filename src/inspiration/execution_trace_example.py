from execution_trace.record import record


@record()
def foo(x, y):
    a = x + y
    return a
