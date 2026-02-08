import atrace  # noqa

x, y = 1, 3

while x < y:
    x = x + 1

print("x:", x)

t = 1, 2


def greet(n):
    message = f"bonjour {n}!"
    return message


print(greet("bob"))
