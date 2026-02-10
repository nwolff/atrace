# TODO

- Do I still need manual teardowns and/or hooks ?
- Thonny, which adds a lot of indirection and magic. Try and find a way to edit the package directly when running in thonny when debugging.

# Nice to have

- Try and show recursive invocations better (materializing the return events in the trace? )
- Don't show "affichage" if there are no output events in the trace
- localize report

# Linting

    uv run ruff check src tests

# Type Checking

    uv run mypy src

# Running unit tests

We use unittest instead of pytest, because pytest's heavy instrumentation of the code causes trouble.

    uv run python -m unittest tests/Test*

# Build

Every time we push a new tag, the package is automatically deployed to pypi:
https://pypi.org/project/atrace/
