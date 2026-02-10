import unittest

import atrace

# XXX: Find a way to assert stuff without too much headache


class TestTracingSimple(unittest.TestCase):
    def test_syntax_error(self):
        atrace.trace_next_loaded_module()

        with self.assertRaises(Exception):
            from .programs import syntax_error  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

    def test_uncaught_exception(self):
        atrace.trace_next_loaded_module()

        with self.assertRaises(Exception):
            from .programs import uncaught_exception  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()

    def test_caught_exception(self):
        atrace.trace_next_loaded_module()

        from .programs import caught_exception  # noqa

        atrace.teardown_vartrace()
        atrace.teardown_outputlogging()
