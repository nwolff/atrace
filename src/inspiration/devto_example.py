import sys


def trace_vars(frame, event, arg):

    if event != "line":
        return trace_vars
    code = frame.f_code
    lineno = frame.f_lineno
    locals_now = frame.f_locals.copy()
    global last_locals

    if code.co_name not in last_locals:
        last_locals[code.co_name] = locals_now
        return trace_vars

    old_locals = last_locals[code.co_name]

    for var, new_val in locals_now.items():
        if var not in old_locals:
            print(f"[{code.co_name}:{lineno}] NEW {var} = {new_val}")
        elif old_locals[var] != new_val:
            print(
                f"[{code.co_name}:{lineno}] MODIFIED {var}: {old_locals[var]} → {new_val}"
            )

    for var in old_locals:
        if var not in locals_now:
            print(f"[{code.co_name}:{lineno}] DELETED {var}")

    last_locals[code.co_name] = locals_now
    return trace_vars


def monitor(func):

    def wrapper(*args, **kwargs):
        global last_locals
        last_locals = {}
        sys.settrace(trace_vars)
        try:
            return func(*args, **kwargs)
        finally:
            sys.settrace(None)

    return wrapper


@monitor
def run_example():
    a = 10
    b = a + 5
    b = b * 2
    del a
    return b


run_example()
