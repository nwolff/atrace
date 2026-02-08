# TODO

- Handle returns (with and without return statements / with and without return values)

- Do I still need manual teardowns and/or hooks ?

- Thonny, which adds a lot of indirection and magic. Try and find a way to edit the package directly when running in thonny when debugging.

# Linting

    uv run ruff check src tests

# Type Checking

    uv run mypy src

# Running unit tests

We don't use pytest because it does a lot of instrumentation in parallel to ours, and it causes a lot of trouble.

    uv run python -m unittest tests/Test*

# Build

Automatically deployed to pypi every time a new tag is pushed: https://pypi.org/project/atrace/
