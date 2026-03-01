import atrace  # noqa

x = 1
x = None  # type: ignore
del [x]
x = "bob"  # type: ignore
