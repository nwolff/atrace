# TODO

- Thonny, which adds a lot of indirection and magic.

- all XXX
- Assert stuff in abrupt termination

- problem when repeating a test
- Get rid of the test specific initialization ?

- cleanup even when exception

- update docs if we remove exit handlers. Emits the trace at the end if the application ends normally and abruptly (
  exception, signal, etc.)

# Linting

    uv run ruff check src tests

# Type Checking

    uv run mypy src tests

# Running unit tests

We use unittest instead of pytest, because pytest's heavy instrumentation of the code causes trouble.

To run all tests:

    uv run python -m unittest discover

To run a single test (module.file.class.method):

    uv run python -m unittest tests.test_simple.TestSimple.test_assignment

# Coverage

    uv run coverage run -m unittest discover

    uv run coverage html

# Translating

## Whenever code changes

    uv run pybabel extract -o locale/atrace.pot src

    uv run pybabel update -i locale/atrace.pot -D atrace -d locale

## To add a language

Here for fr_FR:

    uv run pybabel init -l fr_FR -i locale/atrace.pot -D atrace -d locale

Then edit the newly created .po file

## After modifying any .po file

    uv run pybabel compile -D atrace -d locale

## To verify translations

Here for fr_FR:

    export LANG=fr_FR
    uv run tests/programs/small.py

# Deployment

Every time we push a new tag, the package is automatically deployed to pypi:
https://pypi.org/project/atrace/
