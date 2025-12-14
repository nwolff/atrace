import atrace  # noqa

x, y = 3, 6

while x < y:
    x = x + 1

print("x", x)

t = (1, 2)

kids = ["riri", "fifi", "loulou"]
while kids:
    print(kids.pop(0))


for i in range(3):
    print(i)


def double(a):
    b = a * 2
    return b


print(double(6))


def recursive_count(x):
    if x == 0:
        return 0
    else:
        return 1 + recursive_count(x - 1)


print(recursive_count(4))

answer = input("question ")

raise Exception("an exception")
