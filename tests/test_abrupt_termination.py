import unittest

import atrace


class TestTracingSimple(unittest.TestCase):
    def callback_done(self, trace):
        self.trace = trace

    def test_syntax_error(self):
        atrace.trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .programs import syntax_error  # noqa

    def test_uncaught_exception(self):
        atrace.trace_next_loaded_module(self.callback_done)

        with self.assertRaises(Exception):
            from .programs import uncaught_exception  # noqa

    def test_caught_exception(self):
        atrace.trace_next_loaded_module(self.callback_done)

        from .programs import caught_exception  # noqa
