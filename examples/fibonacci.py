from functools import cache


def fibonacci_iterative(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def fibonacci_recursive(n):
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


@cache
def fibonacci_memoized(n):
    if n <= 1:
        return n
    return fibonacci_memoized(n - 1) + fibonacci_memoized(n - 2)


num = 8
choice = input("(I)terative, (R)ecursive, or (M)emoized: ").upper()

match choice:
    case "I":
        result = fibonacci_iterative(num)
        print(f"Iterative Result: {result}")
    case "R":
        result = fibonacci_recursive(num)
        print(f"Recursive Result: {result}")
    case "M":
        result = fibonacci_memoized(num)
        print(f"Memoized Result: {result}")
    case _:
        print("Invalid choice! Please enter I, R, or M.")
