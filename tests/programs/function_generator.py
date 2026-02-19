import atrace  # noqa


def countdown(n):
    while n > 0:
        yield n
        n -= 1


for num in countdown(2):
    print(num)
