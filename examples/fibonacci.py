from functools import cache


def fib_i(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fib_r(n):
    if n <= 1:
        return n
    return fib_r(n - 1) + fib_r(n - 2)


@cache
def fib_m(n):
    if n <= 1:
        return n
    return fib_m(n - 1) + fib_m(n - 2)


num = 6
choice = input("(I)terative, (R)ecursive, or (M)emoized: ").upper()

match choice:
    case "I":
        result = fib_i(num)
        print(f"Iterative Result: {result}")
    case "R":
        result = fib_r(num)
        print(f"Recursive Result: {result}")
    case "M":
        result = fib_m(num)
        print(f"Memoized Result: {result}")
    case _:
        print("Invalid choice! Please enter I, R, or M.")
