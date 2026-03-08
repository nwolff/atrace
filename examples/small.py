import atrace  # noqa

x, y = 1, 3

while x < y:
    x = x + 1

print("x:", x)


def greet(name):
    message = f"Hi {name}!"
    return message


print(greet("Bob"))
