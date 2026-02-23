import atrace  # noqa


def is_zero(x):
    if x == 0:
        print("zero")
    else:
        print("non-zero")


sum = 0
for a in range(10):
    sum += a

is_zero(sum)

for i in range(20):
    for j in range(i):
        i * j
