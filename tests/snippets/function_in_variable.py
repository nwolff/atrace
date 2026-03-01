import atrace  # noqa


def f(name):
    print("Hello", name)


greet = f

greet("Mike")
