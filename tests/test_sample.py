# import sys

import atrace

# from atrace import model, vartracer

code = """
print("hello")
x = 1
x = x + 1
y, z = 7, 8
"""

trace = atrace.var_trace_for_code(code)
print(trace)
assert 1 == 0  # To show the output
