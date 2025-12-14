import atrace

x = 0
y = 10

while x < y:
    x = x + 1
    y = y - 1
    print("****")

print("x", x)
print("y", x)

l = ["fifi", "riri", "loulou"]
while l:
    print(l.pop())


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
