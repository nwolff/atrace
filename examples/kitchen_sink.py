x, y = 3, 6

while x < y:
    x = x + 1

print("x", x)

t = 1, 2

kids = ["riri", "fifi", "loulou"]
while kids:
    print(kids.pop(0))

lst = [x**2 for x in range(3)]

add = lambda x, y: x + y  # noqa
print(add(5, 3))

for i in range(3):
    print(i)


def recursive_count(x):
    if x == 0:
        return 0
    else:
        return 1 + recursive_count(x - 1)


print(recursive_count(4))

answer = input("question: ")
print(answer)


def countdown(n):
    while n > 0:
        yield n
        n -= 1


for num in countdown(4):
    print(num)


raise Exception("an exception")
