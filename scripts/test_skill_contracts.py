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


class ZshPluginContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read_skill("zsh-plugin")
        self.flat = " ".join(self.text.split())

    def test_names_the_execution_profiles_and_lifecycle(self) -> None:
        for fragment in (
            "sourced-library",
            "autoload-function",
            "isolated",
            "Invoke `<identifier>_plugin_unload`",
            "assert ownership-aware restoration",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.flat)

    def test_scaffolds_from_the_shipped_template_copy(self) -> None:
        self.assertIn("`templates/template.plugin.zsh` in this skill", self.flat)
        self.assertTrue(
            (SKILLS / "zsh-plugin" / "templates" / "template.plugin.zsh").is_file()
        )

    def test_covers_maintenance_and_routes_review_elsewhere(self) -> None:
        for fragment in (
            "## Maintain an existing plugin",
            "### Bring a plugin to Standard 2",
            "### Keep unload exact",
            "### Wire CI",
            "zsh-plugin-reviewer",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)
        self.assertNotIn("disable-model-invocation", self.text)


class ZiDockerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read_skill("zi-docker")

    def test_covers_zi_runs_and_controlled_execution(self) -> None:
        for fragment in (
            "## Run Zi in a container",
            "make shell",
            "`zi_repo` and `zi_ref`",
            "## Controlled Zsh execution",
            "`runtime` for source tests or `module-build`",
            "execution.json",
            "grants no publication or external-write authority",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.text)

    def test_links_zd_docs_at_pinned_commits(self) -> None:
        for link in self.text.split("https://github.com/z-shell/zd/blob/")[1:]:
            with self.subTest(link=link[:60]):
                self.assertRegex(link, r"^[0-9a-f]{40}/")


class ZiInstallContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = read_skill("zi-install")

    def test_is_user_invoked_in_both_runtimes(self) -> None:
        self.assertIn(
            "\ndisable-model-invocation: true\n",
            self.text.split("\n---\n", 1)[0] + "\n",
        )
        policy = (SKILLS / "zi-install" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("allow_implicit_invocation: false", policy)

    def test_keeps_the_installer_safety_contract(self) -> None:
        for fragment in (
            "Do not write `.zshrc`",
            "published installer checksums",
            "Stop on a mismatch or on a missing line",
            "zi-setup-result-v1",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, " ".join(self.text.split()))


if __name__ == "__main__":
    unittest.main()
