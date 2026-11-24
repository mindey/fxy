import sys
import unittest
from unittest import mock

import fxy


class RuntimeTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(fxy.__version__, "0.8.1")

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
            with self.assertRaisesRegex(RuntimeError, r"fxy\[ipython\]"):
                fxy.interact(("calc",), mode=True)

    def test_module_expression_uses_calc_namespace(self):
        import contextlib
        import io
        import runpy

        output = io.StringIO()
        argv = ["fxy", "os.path.basename('/a/b')"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
            runpy.run_module("fxy", run_name="__main__")

        self.assertEqual(output.getvalue().strip(), "b")


if __name__ == "__main__":
    unittest.main()
