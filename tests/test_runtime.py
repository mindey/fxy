import importlib.util
import sys
import unittest
from unittest import mock

import fxy


class RuntimeTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(fxy.__version__, "0.8.2")

    def test_plain_interact_uses_current_interpreter(self):
        with mock.patch("fxy.subprocess.run") as run:
            fxy.interact(("calc",), mode=False)

        command = run.call_args.args[0]
        self.assertEqual(command[0], sys.executable)
        self.assertEqual(command[1:3], ["-i", "-c"])
        self.assertIn("from fxy.calc import *", command[3])

    def test_ipython_missing_has_actionable_error(self):
        original = fxy.importlib.util.find_spec

        def find_spec(name):
            if name == "IPython":
                return None
            return original(name)

        with mock.patch("fxy.importlib.util.find_spec", side_effect=find_spec):
            with self.assertRaisesRegex(RuntimeError, r"IPython package"):
                fxy.interact(("calc",), mode=True)

    def test_module_expression_requires_calc_profile(self):
        import contextlib
        import io
        import runpy

        original = importlib.util.find_spec

        def find_spec(name):
            if name in {"mpmath", "eday"}:
                return None
            return original(name)

        error = io.StringIO()
        argv = ["fxy", "pi**2"]
        with mock.patch.object(sys, "argv", argv):
            with mock.patch("importlib.util.find_spec", side_effect=find_spec):
                with contextlib.redirect_stderr(error):
                    with self.assertRaises(SystemExit) as caught:
                        runpy.run_module("fxy", run_name="__main__")

        self.assertEqual(caught.exception.code, 2)
        self.assertIn("fxy.install('calc', approve=True)", error.getvalue())


if __name__ == "__main__":
    unittest.main()
