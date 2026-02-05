import atrace  # noqa

x, y = 1, 3

while x < y:
    x = x + 1

print("x:", x)

t = 1, 2


def f(a, b):
    c = a + " " + b
    return c + "!"


print(f("Bonjour", "tout le monde"))
