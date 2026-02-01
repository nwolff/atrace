import atrace  # noqa

x, y = 1, 3

while y > 0:
    x = x + 1
    y = y - 1

print("somme: ", x)


def f(a, b):
    c = a + " " + b
    print(c, "!")


f("Bonjour", "tout le monde")
