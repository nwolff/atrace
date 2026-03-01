import atrace  # noqa

print("hai")
x = 1
raise Exception("an exception")

print("we never get here")  # noqa
