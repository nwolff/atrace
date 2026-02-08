import atrace  # noqa

print("hai")
try:
    raise Exception("an exception")
except Exception as e:
    print(e)
