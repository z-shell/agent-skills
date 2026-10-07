#!/usr/bin/env python3
"""Tests for scripts/catalog.py."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("catalog.py")
SPEC = importlib.util.spec_from_file_location("catalog", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)

BASE = {
    "version": "0.1.0",
    "marketplace": {
        "name": "z-shell",
        "displayName": "Z-Shell",
        "description": "Skills.",
        "owner": {"name": "Z-Shell", "url": "https://github.com/z-shell"},
    },
    "plugins": [
        {
            "name": "z-shell",
            "displayName": "Z-Shell",
            "description": "Skills for Zsh.",
            "category": "Productivity",
            "keywords": ["zsh"],
            "skills": ["zunit"],
        }
    ],
}
SKILL = "---\nname: {name}\ndescription: Write and run ZUnit tests.\n{extra}---\n\n# ZUnit\n\nBody.\n"


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.data = copy.deepcopy(BASE)
        self.write_skill("z-shell", "zunit")

    def write_catalog(self) -> None:
        (self.root / "catalog.json").write_text(json.dumps(self.data), encoding="utf-8")

    def write_skill(
        self, plugin: str, name: str, extra: str = "", body_name: str | None = None
    ) -> Path:
        directory = self.root / "plugins" / plugin / "skills" / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(
            SKILL.format(name=body_name or name, extra=extra), encoding="utf-8"
        )
        return directory

    def run_catalog(self, *arguments: str) -> tuple[int, str]:
        self.write_catalog()
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = catalog.main(["--root", str(self.root), *arguments])
        return status, output.getvalue()

    def assert_fails(self, expected: str) -> None:
        status, output = self.run_catalog()
        self.assertEqual(status, 1, output)
        self.assertIn(expected, output)

    def test_generate_then_check(self) -> None:
        status, output = self.run_catalog("--check")
        self.assertEqual(status, 1)
        self.assertIn("differs from catalog.json", output)
        self.assertEqual(self.run_catalog()[0], 0)
        self.assertEqual(
            self.run_catalog("--check"), (0, "4 manifests match catalog.json\n")
        )
        claude = json.loads((self.root / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(claude["plugins"][0]["source"], "./plugins/z-shell")
        self.assertEqual(claude["metadata"]["version"], "0.1.0")
        codex = json.loads((self.root / ".agents/plugins/marketplace.json").read_text())
        self.assertEqual(
            codex["plugins"][0]["source"],
            {"source": "local", "path": "./plugins/z-shell"},
        )
        self.assertEqual(codex["plugins"][0]["policy"]["installation"], "AVAILABLE")
        portable = json.loads((self.root / "plugins/z-shell/plugin.json").read_text())
        self.assertEqual(portable["$schema"], catalog.AGENT_PLUGINS_SCHEMA)
        self.assertEqual(portable["version"], "0.1.0")
        self.assertEqual(portable["license"], "MIT")
        native = json.loads(
            (self.root / "plugins/z-shell/.claude-plugin/plugin.json").read_text()
        )
        self.assertNotIn("$schema", native)
        self.assertEqual(native["name"], "z-shell")

    def test_version_bump_is_drift_until_regenerated(self) -> None:
        self.run_catalog()
        self.data["version"] = "0.2.0"
        status, output = self.run_catalog("--check")
        self.assertEqual(status, 1)
        self.assertIn("plugins/z-shell/plugin.json: differs", output)

    def test_check_writes_nothing(self) -> None:
        self.run_catalog("--check")
        self.assertFalse((self.root / ".claude-plugin").exists())

    def test_catalog_schema(self) -> None:
        cases = {
            "version must be MAJOR.MINOR.PATCH": lambda d: d.update(version="1.0"),
            "must be kebab-case and not reserved": lambda d: d["marketplace"].update(
                name="agent-skills"
            ),
            "owner needs a name": lambda d: d["marketplace"].update(owner={}),
            "skills must be a sorted list": lambda d: d["plugins"][0].update(
                skills=["zunit", "zd"]
            ),
            "top-level keys": lambda d: d.update(extra=1),
        }
        original = copy.deepcopy(self.data)
        for expected, mutate in cases.items():
            with self.subTest(expected=expected):
                self.data = copy.deepcopy(original)
                mutate(self.data)
                self.assert_fails(expected)

    def test_skill_belongs_to_one_plugin(self) -> None:
        self.data["plugins"].append(
            {**copy.deepcopy(BASE["plugins"][0]), "name": "other"}
        )
        self.write_skill("other", "zunit")
        self.assert_fails("a skill belongs to exactly one plugin")

    def test_unlisted_and_missing_skills(self) -> None:
        self.write_skill("z-shell", "zd")
        self.assert_fails("plugins/z-shell/skills/zd: not listed in catalog.json")
        self.data["plugins"][0]["skills"] = ["zd", "zi", "zunit"]
        self.assert_fails("skill zi has no directory")

    def test_unlisted_plugin_directory(self) -> None:
        (self.root / "plugins" / "stray").mkdir(parents=True)
        self.assert_fails("plugins/stray: plugin directory is not in catalog.json")

    def test_skill_names(self) -> None:
        for name, expected in (
            ("zi-agent", "generic word 'agent'"),
            ("helper", "generic word 'helper'"),
            ("Zi_Install", "lowercase letters, digits and single hyphens"),
        ):
            with self.subTest(name=name):
                self.data["plugins"][0]["skills"] = sorted(["zunit", name])
                self.write_skill("z-shell", name)
                self.assert_fails(expected)
                for path in sorted(
                    (self.root / "plugins/z-shell/skills" / name).rglob("*"),
                    reverse=True,
                ):
                    path.unlink()
                (self.root / "plugins/z-shell/skills" / name).rmdir()

    def test_frontmatter_name_must_match(self) -> None:
        self.write_skill("z-shell", "zunit", body_name="zunit-test")
        self.assert_fails("frontmatter name 'zunit-test' must be 'zunit'")

    def test_invocation_flags_must_agree(self) -> None:
        directory = self.write_skill(
            "z-shell", "zunit", extra="disable-model-invocation: true\n"
        )
        self.assert_fails("must set policy.allow_implicit_invocation: false")
        (directory / "agents").mkdir()
        (directory / "agents/openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8"
        )
        self.assertEqual(self.run_catalog()[0], 0)
        self.write_skill("z-shell", "zunit")
        self.assert_fails("must set disable-model-invocation: true")

    def test_parent_links_are_rejected(self) -> None:
        directory = self.write_skill("z-shell", "zunit")
        (directory / "references").mkdir()
        (directory / "references/notes.md").write_text(
            "See [zd](../../zd/SKILL.md).\n", encoding="utf-8"
        )
        self.assert_fails("references/notes.md:1: links outside the skill with ../")

    def test_repository_catalog_is_current(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = catalog.main(["--check"])
        self.assertEqual(status, 0, output.getvalue())


if __name__ == "__main__":
    unittest.main()
