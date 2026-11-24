import os
import sys
import tempfile
import unittest
from unittest import mock

import fxy


PROFILE = """\
__fxy_profile__ = 1
__requires__ = ["example>=1"]

import math as m
from math import pi
from math import sqrt as root
"""


class FxyTests(unittest.TestCase):
    def setUp(self):
        self.cache = tempfile.TemporaryDirectory()
        self.environment = mock.patch.dict(
            os.environ, {"FXY_CACHE_DIR": self.cache.name}
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.cache.cleanup()

    @staticmethod
    def response(text=PROFILE):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = text.encode()
        response.__exit__.return_value = False
        return response

    def test_describe_is_static(self):
        with mock.patch("fxy.urlopen", return_value=self.response()):
            info = fxy.describe("mindey/example")

        self.assertEqual(info["source"], "mindey/example")
        self.assertEqual(info["requirements"], ("example>=1",))
        self.assertEqual(info["bindings"], ("m", "pi", "root"))
        self.assertEqual(len(info["sha256"]), 64)

    def test_source_can_be_pinned(self):
        with mock.patch("fxy.urlopen", return_value=self.response()):
            info = fxy.describe("mindey/example@v1")

        self.assertEqual(info["source"], "mindey/example@v1")
        self.assertIn("/mindey/example/v1/fxy.py", info["url"])

    def test_source_rejects_path_traversal_ref(self):
        with self.assertRaises(ValueError):
            fxy.describe("mindey/example@../../main")

    def test_profile_requires_schema_marker(self):
        with mock.patch(
            "fxy.urlopen", return_value=self.response("import math\n")
        ):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_profile_syntax_errors_are_invalid_profiles(self):
        text = "__fxy_profile__ = 1\nfrom\n"
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_describe_does_not_import_declared_modules(self):
        text = (
            "__fxy_profile__ = 1\n"
            "__requires__ = ['definitely-not-installed>=1']\n"
            "import definitely_not_installed\n"
        )
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            info = fxy.describe("mindey/missing")

        self.assertEqual(info["bindings"], ("definitely_not_installed",))
        self.assertEqual(info["requirements"], ("definitely-not-installed>=1",))

    def test_profile_rejects_executable_statements(self):
        text = "__fxy_profile__ = 1\nprint('no')\n"
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_profile_rejects_relative_imports(self):
        text = "__fxy_profile__ = 1\nfrom .local import thing\n"
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_profile_rejects_duplicate_metadata(self):
        text = (
            "__fxy_profile__ = 1\n"
            "__fxy_profile__ = 1\n"
            "import math\n"
        )
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_profile_rejects_pip_options_as_requirements(self):
        text = (
            "__fxy_profile__ = 1\n"
            "__requires__ = ['--extra-index-url=https://example.invalid']\n"
            "import math\n"
        )
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.InvalidProfile):
                fxy.describe("mindey/example")

    def test_fetch_is_cached(self):
        with mock.patch("fxy.urlopen", return_value=self.response()) as opened:
            first = fxy.describe("mindey/example")
            second = fxy.describe("mindey/example")

        self.assertEqual(first["sha256"], second["sha256"])
        self.assertEqual(opened.call_count, 1)

    def test_refresh_replaces_cache(self):
        first = "__fxy_profile__ = 1\nimport math\n"
        second = "__fxy_profile__ = 1\nimport cmath\n"
        with mock.patch(
            "fxy.urlopen",
            side_effect=[self.response(first), self.response(second)],
        ):
            old = fxy.describe("mindey/example")
            new = fxy.describe("mindey/example", refresh=True)

        self.assertNotEqual(old["sha256"], new["sha256"])
        self.assertEqual(new["bindings"], ("cmath",))

    def test_refresh_falls_back_to_cache_when_offline(self):
        with mock.patch("fxy.urlopen", return_value=self.response()):
            first = fxy.describe("mindey/example")

        with mock.patch("fxy.urlopen", side_effect=OSError("offline")):
            second = fxy.describe("mindey/example", refresh=True)

        self.assertEqual(first["sha256"], second["sha256"])

    def test_namespace_realizes_python_import_semantics(self):
        with mock.patch("fxy.urlopen", return_value=self.response()):
            values = fxy.namespace("mindey/example")

        self.assertEqual(values["root"](9), 3)
        self.assertAlmostEqual(values["m"].pi, 3.141592653589793)
        self.assertNotIn("__builtins__", values)

    def test_star_import_uses_python_semantics(self):
        text = "__fxy_profile__ = 1\nfrom math import *\n"
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            values = fxy.namespace("mindey/example")

        self.assertEqual(values["sqrt"](16), 4)

    def test_missing_dependency_has_install_hint(self):
        text = (
            "__fxy_profile__ = 1\n"
            "__requires__ = ['definitely-not-an-installed-fxy-test-package>=1']\n"
            "import definitely_not_an_installed_fxy_test_package\n"
        )
        with mock.patch("fxy.urlopen", return_value=self.response(text)):
            with self.assertRaises(fxy.MissingDependency) as caught:
                fxy.namespace("mindey/missing")

        message = str(caught.exception)
        self.assertIn(
            "definitely-not-an-installed-fxy-test-package>=1", message
        )
        self.assertIn("fxy.install('mindey/missing')", message)

    def test_use_can_target_explicit_mapping(self):
        target = {"existing": object()}
        existing = target["existing"]

        with mock.patch("fxy.urlopen", return_value=self.response()):
            injected = fxy.use("mindey/example", target)

        self.assertIs(target["existing"], existing)
        self.assertEqual(target["root"](25), 5)
        self.assertEqual(set(injected), {"m", "pi", "root"})

    def test_use_defaults_to_callers_globals(self):
        target = {}
        with mock.patch("fxy.urlopen", return_value=self.response()):
            exec("import fxy\nfxy.use('mindey/example')", target)

        self.assertEqual(target["root"](36), 6)

    def test_install_is_the_explicit_mutation_boundary(self):
        with mock.patch("fxy.urlopen", return_value=self.response()), mock.patch(
            "fxy.subprocess.run"
        ) as run:
            requirements = fxy.install("mindey/example")

        self.assertEqual(requirements, ("example>=1",))
        command = run.call_args.args[0]
        self.assertEqual(command[:4], [sys.executable, "-m", "pip", "install"])
        self.assertEqual(command[4:], ["example>=1"])
        self.assertTrue(run.call_args.kwargs["check"])

    def test_install_does_nothing_without_requirements(self):
        text = "__fxy_profile__ = 1\nimport math\n"
        with mock.patch("fxy.urlopen", return_value=self.response(text)), mock.patch(
            "fxy.subprocess.run"
        ) as run:
            requirements = fxy.install("mindey/example")

        self.assertEqual(requirements, ())
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
