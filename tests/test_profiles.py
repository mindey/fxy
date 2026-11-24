import unittest

import fxy
from fxy.profiles import Profile


class ProfileTests(unittest.TestCase):
    def test_available_profiles_are_versioned(self):
        self.assertEqual(fxy.available(), ("calc/v1", "cas/v1", "lab/v1"))

    def test_aliases_resolve_to_versioned_contracts(self):
        self.assertEqual(fxy.resolve("cas"), fxy.resolve("cas/v1"))
        self.assertEqual(fxy.resolve("lab").id, "lab/v1")

    def test_names_match_legacy_star_import_rule(self):
        import fxy.calc as calc

        expected = tuple(
            sorted(name for name in vars(calc) if not name.startswith("_"))
        )
        self.assertEqual(fxy.names("calc/v1"), expected)

    def test_namespace_is_non_mutating(self):
        values = fxy.namespace("calc")
        self.assertEqual(set(values), set(fxy.names("calc")))

    def test_use_can_target_explicit_mapping(self):
        target = {"existing": object()}
        existing = target["existing"]

        injected = fxy.use("calc", target)

        self.assertIs(target["existing"], existing)
        self.assertEqual(set(injected), set(fxy.names("calc")))
        self.assertTrue(set(injected).issubset(target))

    def test_diff_is_symmetric_for_added_and_removed(self):
        forward = fxy.diff("calc/v1", "cas/v1")
        reverse = fxy.diff("cas/v1", "calc/v1")

        self.assertEqual(set(forward["added"]), set(reverse["removed"]))
        self.assertEqual(set(forward["removed"]), set(reverse["added"]))

    def test_profile_metadata_is_inspectable(self):
        info = fxy.describe("cas")

        self.assertEqual(info["id"], "cas/v1")
        self.assertEqual(info["module"], "fxy.cas")
        self.assertIsInstance(fxy.resolve("cas"), Profile)
        self.assertEqual(tuple(info["names"]), fxy.names("cas"))

    def test_root_use_preserves_interactive_caller_namespace(self):
        target = {}
        exec("import fxy\nfxy.use('calc')", target)
        self.assertTrue(set(fxy.names("calc")).issubset(target))


if __name__ == "__main__":
    unittest.main()
