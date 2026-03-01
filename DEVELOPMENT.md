# TODO

Add a view with an animated trace, with the current state visible. Maybe the old
state flies away ?

## Maybe

- Localized README. [English](README.md) | [Français](README.fr.md)
- Speed control / Manual nav / Automaticaly determine the best animation length
- Capture the animation with Ascii-cinema / moviepy / console.save_svg
- Fix jitter in animated_histogram when scrolling (video game camera technique)
- Show activations ? Just the depth ?

# Development

We use uv for development.

## Running example programs

With cpython:

    uv run examples/small.py

With pypy:

    uv run --python pypy examples/small.py

## Type Checking

    uv run mypy src tests

## Linting

    uv run ruff check src tests examples --fix

## Code formating

    uv run ruff format

## Running unit tests

We use unittest instead of pytest, because pytest's heavy instrumentation of the code
causes trouble.

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
    uv run example_programs/small.py

## Developing for Thonny

Thonny installs packages in the user specific python library directory:

On mac it's something like: ~/Library/Python/3.10/lib/python/site-packages

## Deployment

Every time we push to main, the code is checked and unittests are run.

Every time we push a new tag, the package gets automatically deployed to pypi:
https://pypi.org/project/atrace/
