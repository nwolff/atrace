import atrace  # noqa

c = "start"


def f(a, b):
    global c
    c = a + b
    return c


x = f(3, 14) * 2
