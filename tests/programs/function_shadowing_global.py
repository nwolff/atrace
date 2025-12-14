import atrace  # noqa

c = "start"


def f(a, b):
    c = a + b
    return c


x = f(3, 14) * 2
