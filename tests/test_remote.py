from pathlib import Path
import tempfile
import unittest
from unittest import mock

import fxy
from fxy import remote


PROFILE = """\
__fxy_profile__ = 1
__requires__ = ["mathlib>=1"]

import math as m
from math import sqrt as root
from math import pi
"""


class RemoteProfileTests(unittest.TestCase):
    def test_source_syntax(self):
        source = remote.parse_source("mindey/cas@main")
        self.assertEqual((source.owner, source.repo, source.ref), ("mindey", "cas", "main"))
        self.assertEqual(remote.parse_source("mindey/cas").ref, "HEAD")
        self.assertTrue(remote.is_source("mindey/cas"))
        # cas/v1 also has the syntactic owner/repo shape; public fxy
        # resolution gives registered canonical profiles precedence.
        self.assertTrue(remote.is_source("cas/v1"))

    def test_profile_requires_explicit_schema(self):
        source = remote.parse_source("mindey/cas")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(remote.InvalidRemoteProfile):
                remote._parse("import math\n", source, Path(td) / "fxy.py")

    def test_source_rejects_path_traversal_ref(self):
        with self.assertRaises(ValueError):
            remote.parse_source("mindey/cas@../../master")

    def test_profile_rejects_executable_statements(self):
        source = remote.parse_source("mindey/cas")
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(remote.InvalidRemoteProfile):
                remote._parse("print('no')\n", source, Path(td) / "fxy.py")

    def test_fetch_caches_profile(self):
        payload = PROFILE.encode()
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = payload
        response.__exit__.return_value = False
        with tempfile.TemporaryDirectory() as td, mock.patch(
            "fxy.remote.urlopen", return_value=response
        ) as opened:
            first = remote.fetch("mindey/cas", cache_dir=Path(td))
            second = remote.fetch("mindey/cas", cache_dir=Path(td))
        self.assertEqual(first.sha256, second.sha256)
        self.assertEqual(opened.call_count, 1)

    def test_namespace_realizes_imports(self):
        with tempfile.TemporaryDirectory() as td:
            source = remote.parse_source("mindey/cas")
            path = remote._cache_path(source, Path(td))
            path.parent.mkdir(parents=True)
            path.write_text(PROFILE)
            values = remote.namespace("mindey/cas", cache_dir=Path(td))

        self.assertIs(values["m"], __import__("math"))
        self.assertEqual(values["root"](9), 3)
        self.assertAlmostEqual(values["pi"], 3.141592653589793)

    def test_remote_and_builtin_share_install_approval_type(self):
        from fxy.dependencies import InstallApprovalRequired
        self.assertIs(remote.InstallApprovalRequired, InstallApprovalRequired)

    def test_install_requires_approval(self):
        with tempfile.TemporaryDirectory() as td:
            source = remote.parse_source("mindey/cas")
            path = remote._cache_path(source, Path(td))
            path.parent.mkdir(parents=True)
            path.write_text(PROFILE)
            with self.assertRaises(remote.InstallApprovalRequired):
                remote.install("mindey/cas", cache_dir=Path(td))

    def test_root_use_dispatches_remote_profile(self):
        with tempfile.TemporaryDirectory() as td:
            source = remote.parse_source("mindey/cas")
            path = remote._cache_path(source, Path(td))
            path.parent.mkdir(parents=True)
            path.write_text(PROFILE)
            target = {}
            fxy.use("mindey/cas", target, cache_dir=Path(td))
        self.assertEqual(target["root"](16), 4)

    def test_builtin_profile_takes_precedence_over_github_shape(self):
        self.assertEqual(fxy.describe("cas/v1")["id"], "cas/v1")

    def test_missing_dependency_error_names_requirements(self):
        profile = (
            "__fxy_profile__ = 1\n"
            "__requires__ = ['definitely-not-an-installed-fxy-test-package>=1']\n"
            "import definitely_not_an_installed_fxy_test_package\n"
        )
        with tempfile.TemporaryDirectory() as td:
            source = remote.parse_source("mindey/missing")
            path = remote._cache_path(source, Path(td))
            path.parent.mkdir(parents=True)
            path.write_text(profile)
            with self.assertRaises(remote.ProfileDependencyError) as caught:
                remote.namespace("mindey/missing", cache_dir=Path(td))
        message = str(caught.exception)
        self.assertIn("definitely-not-an-installed-fxy-test-package>=1", message)
        self.assertIn("approve=True", message)


if __name__ == "__main__":
    unittest.main()
