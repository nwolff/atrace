import atrace  # noqa

x, y = 1, 3

while x < y:
    x = x + 1

print("x:", x)

t = 1, "a"


def greet(name):
    message = f"Hello {name}!"
    return message


print(greet("Bob"))
