#!/usr/bin/env python3
"""Content contracts for published skills.

These assertions moved here with the skills they cover (ADR-0037 in
z-shell/.github). The organization's Zsh Policy Consumers check covers the
canonical references; these cover what each skill must still teach.
"""

from __future__ import annotations

import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / "plugins" / "z-shell" / "skills"


def read_skill(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


class ZunitContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read_skill("zunit")

    def test_names_the_test_contract_rules(self) -> None:
        for fragment in (
            "test-fixture",
            "zsh/test/isolate-environment",
            "zsh/test/match-production-profile",
            "zsh/plugin/exact-lifecycle",
            "Declare each intentional negative fixture",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)

    def test_example_guards_and_demonstrates_unload_lifecycle(self) -> None:
        for fragment in (
            "if (( ${+functions[my_plugin_plugin_unload]} )); then",
            "@test 'unload restores owned state and self-destructs'",
            "assert before plugin_load_surface loaded",
            "assert before plugin_unloaded loaded user_state after",
            "one `@setup` and one `@teardown`, each running around every test",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)
        self.assertNotIn("typeset -gA Plugins", self.text)

    def test_defines_plugins_restoration_as_preload_state(self) -> None:
        self.assertIn("pre-load state", " ".join(self.text.split()))


if __name__ == "__main__":
    unittest.main()
