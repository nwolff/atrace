import atrace  # noqa

x, y = 1, 3

print("haaaa")

while x < y:
    x = x + 1

print("x:", x)


def f(a, b):
    c = a + " " + b
    print(c, "!")


f("Bonjour", "tout le monde")
