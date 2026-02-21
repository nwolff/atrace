## Running example programs

With cpython:

    uv run tests/programs/small_example.py

With pypy:

    uv run --python pypy tests/programs/small_example.py

## Linting

    uv run ruff check src tests

## Type Checking

    uv run mypy src tests

## Running unit tests

We use unittest instead of pytest, because pytest's heavy instrumentation of the code causes trouble.

To run all tests:

    uv run python -m unittest discover

To run a single test (_module.file.class.method_):

    uv run python -m unittest tests.test_simple.TestSimple.test_assign_then_print

## Coverage

    uv run coverage run -m unittest discover

    uv run coverage html

## Translating

### Whenever code changes

    uv run pybabel extract -o src/atrace/locale/atrace.pot src

    uv run pybabel update -i src/atrace/locale/atrace.pot -D atrace -d src/atrace/locale

### To add a language

Here for german:

    uv run pybabel init -l de -i src/atrace/locale/atrace.pot -D atrace -d src/atrace/locale

Then edit the newly created .po file

### After adding/modifying any .po file

    uv run pybabel compile -D atrace -d src/atrace/locale

### To verify translations

Here for fr:

    export LANG=fr
    uv run tests/programs/small_example.py

## Developing for Thonny

Thonny installs packages in the user specific python library directory:

On mac it's something like: ~/Library/Python/3.10/lib/python/site-packages

## Deployment

Every time we push to main, the code is checked and unittests are run.

Every time we push a new tag, the package gets automatically deployed to pypi:
https://pypi.org/project/atrace/
