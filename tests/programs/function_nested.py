import atrace  # noqa


def outer(x):
    y = x + 1

    def inner(a):
        x = y + a
        return x

    return inner(x * 2)


result = outer(4)
