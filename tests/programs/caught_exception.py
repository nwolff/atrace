import atrace  # noqa

try:
    raise Exception("error message")
except Exception as e:
    print(e)
