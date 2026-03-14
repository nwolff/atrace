def is_even(n):
    match n:
        case 0:
            return True
        case _:
            return is_odd(n - 1)


def is_odd(n):
    match n:
        case 0:
            return False
        case _:
            return is_even(n - 1)


print(is_even(5))
