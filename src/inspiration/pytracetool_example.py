from pytracertool.pytracertool import CodeTracer

example_code = """
x = 1
y = 1
x = x + y
print(x)
"""

tracer = CodeTracer(example_code, None)
tracer.generate_trace_table()
trace_table_str = str(tracer)
print(trace_table_str)
