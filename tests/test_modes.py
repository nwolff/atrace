import os
import sys
import unittest
from contextlib import contextmanager
from pprint import pprint
from typing import Any

"""
We support 4 modes of operation:
- Running atrace on non-instrumented code. Other unit tests do this.
- Instrumented .py file run from a standard python interpreter
- Instrumented .py file in thonny
- Instrumented unsaved code in the thonny editor

How thonny executes code :
https://github.com/thonny/thonny/blob/653c001bf0a1971df0f563ac7bdbc8849b23cf3b/thonny/plugins/cpython_backend/cp_back.py#L785

"""

INSTRUMENTED_CODE = """
import atrace

print("Hello!")
"""


class TestModes(unittest.TestCase):
    def on_trace(self, trace):
        self.trace = trace

    def test_interpreter_instrumented_file(self):
        with fresh_import("atrace"):
            os.environ["STORE_TRACE"] = "TRUE"
            from .snippets import instrumented  # noqa

            atrace = sys.modules.get("atrace")
            trace = atrace._trace
            pprint(trace)

    def test_thonny_instrumented_file(self):
        with fresh_import("atrace"):
            os.environ["STORE_TRACE"] = "TRUE"

            # XXX: Need to look in the thonny source code how this is done

    def test_thonny_intrumented_buffer(self):
        with fresh_import("atrace"):
            os.environ["STORE_TRACE"] = "TRUE"

            # This is how thonny runs code that is in the editor buffer
            namespace: dict[Any, Any | None] = {}
            exec(INSTRUMENTED_CODE, namespace)

            atrace = sys.modules.get("atrace")
            trace = atrace._trace
            expected_trace = [
                (0, atrace.TCall({}, {}, "<module>")),
                (1, atrace.TLine({}, {})),
                (1, atrace.TOutput("Hello\n")),
                (1, atrace.TReturn({}, {}, None)),
            ]
            self.assertEqual(expected_trace, trace)


@contextmanager
def fresh_import(package_prefix):
    """
    Unloads all modules matching the prefix before and after
    the wrapped block to ensure a fresh import state.
    """

    def _unload():
        # We use list() because we are modifying the dict during iteration
        for mod_name in list(sys.modules.keys()):
            if mod_name == package_prefix or mod_name.startswith(package_prefix + "."):
                del sys.modules[mod_name]

    _unload()  # Clear before
    try:
        yield
    finally:
        _unload()  # Clear after
