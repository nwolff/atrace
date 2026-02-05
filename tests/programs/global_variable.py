import atrace  # noqa

c = "first value of c"


def f(a, b):
    global c
    c = a + b
    d = a - b
    return c, d


print(f(3, 14))
