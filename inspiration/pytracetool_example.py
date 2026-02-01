from pytracertool.pytracertool import CodeTracer

example_code = """
x = 0
y = 10

while x < y:
    x = x + 1
    y = y - 1
    print("****")

print("x", x)
print("y", x)

l = ["fifi", "riri", "loulou"]
while l:
    print(l.pop())


def double(a):
    b = a * 2
    return b


print(double(6))


'''
def recursive_count(x):
    if x == 0:
        return 0
    else:
        return 1 + recursive_count(x - 1)


print(recursive_count(4))
'''
"""

# pytracetool chokes trying to deepcopy some objects. To run this code you'll have to patch the installed pytracetool package
tracer = CodeTracer(example_code, None)
tracer.generate_trace_table()
trace_table_str = str(tracer)
print(trace_table_str)
