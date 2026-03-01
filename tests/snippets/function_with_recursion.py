import atrace  # noqa


def sum_up_to(x):
    return 0 if x == 0 else x + sum_up_to(x - 1)


result = sum_up_to(2)
