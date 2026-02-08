import atrace  # noqa

lst = ["a", "b"]
while lst:
    print(lst.pop(0))  # A print and a mutation at the same time, oh my
