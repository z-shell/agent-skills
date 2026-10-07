#!/usr/bin/env python3
"""Generate and check the plugin manifests from catalog.json (ADR-0037).

catalog.json is the only hand-edited package metadata. This script writes:

- .claude-plugin/marketplace.json        Claude Code marketplace
- .agents/plugins/marketplace.json       Codex repository marketplace
- plugins/<plugin>/plugin.json           portable Agent Plugins manifest
- plugins/<plugin>/.claude-plugin/plugin.json  Claude Code plugin manifest

It also enforces the skill rules from z-shell/.github
knowledge/domains/agents/skill-naming.md and ADR-0037: each skill lives in
exactly one plugin, its directory, frontmatter name and catalog entry agree,
its name follows the Agent Skills format without a generic word, its two
invocation flags agree, and it reaches other skills by name, never by a
``../`` link.

Usage:
    python3 scripts/catalog.py           write the manifests
    python3 scripts/catalog.py --check   report drift and rule violations, write nothing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "catalog.json"
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
REPOSITORY_URL = "https://github.com/z-shell/agent-skills"
LICENSE = "MIT"

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
# Generic words a skill name may not be or end with (skill-naming.md).
GENERIC_WORDS = ("agent", "helper", "tools", "utils", "skill")
# Marketplace names Claude Code reserves (plugins/marketplace-reference).
RESERVED_MARKETPLACES = {
    "agent-skills",
    "anthropic-agent-skills",
    "anthropic-marketplace",
    "anthropic-plugins",
    "claude-code-marketplace",
    "claude-code-plugins",
    "claude-plugins-official",
}
PARENT_LINK = re.compile(r"\]\(\s*<?\.\./")
MAX_DESCRIPTION = 1024


class CatalogError(Exception):
    pass


def dump(data: object) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def parse_scalar(value: str) -> object:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value in ("true", "false"):
        return value == "true"
    return value


def parse_simple_yaml(text: str) -> dict:
    """Parse the block mappings of scalars used by SKILL.md and agents/openai.yaml.

    Only ``key: value`` lines and nested mappings introduced by ``key:`` are
    read; lists and multi-line scalars are skipped. That covers every field
    this checker reads.
    """
    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]
    for raw in text.splitlines():
        if (
            not raw.strip()
            or raw.lstrip().startswith("#")
            or raw.lstrip().startswith("- ")
        ):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, separator, value = raw.strip().partition(":")
        if not separator:
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() in ("", "|", ">", "|-", ">-"):
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(value)
    return root


def frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return parse_simple_yaml("\n".join(lines[1:index]))
    raise ValueError("unterminated YAML frontmatter")


def load_catalog(root: Path) -> dict:
    try:
        catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"{CATALOG}: {exc}") from exc
    errors: list[str] = []
    if set(catalog) != {"version", "marketplace", "plugins"}:
        errors.append(
            f"{CATALOG}: top-level keys must be version, marketplace and plugins"
        )
    if not VERSION_PATTERN.fullmatch(str(catalog.get("version", ""))):
        errors.append(f"{CATALOG}: version must be MAJOR.MINOR.PATCH")
    market = catalog.get("marketplace") or {}
    name = market.get("name", "")
    if not NAME_PATTERN.fullmatch(name) or name in RESERVED_MARKETPLACES:
        errors.append(
            f"{CATALOG}: marketplace name {name!r} must be kebab-case and not reserved"
        )
    for field in ("displayName", "description"):
        if not isinstance(market.get(field), str) or not market[field]:
            errors.append(f"{CATALOG}: marketplace needs {field}")
    owner = market.get("owner") or {}
    if not owner.get("name"):
        errors.append(f"{CATALOG}: marketplace owner needs a name")
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{CATALOG}: plugins must be a non-empty list")
        plugins = []
    seen_plugins: set[str] = set()
    seen_skills: dict[str, str] = {}
    for plugin in plugins:
        pname = plugin.get("name", "")
        if not NAME_PATTERN.fullmatch(pname) or pname in seen_plugins:
            errors.append(f"{CATALOG}: plugin name {pname!r} must be unique kebab-case")
        seen_plugins.add(pname)
        for field in ("displayName", "description", "category"):
            if not isinstance(plugin.get(field), str) or not plugin[field]:
                errors.append(f"{CATALOG}: plugin {pname} needs {field}")
        keywords = plugin.get("keywords", [])
        if not isinstance(keywords, list) or not all(
            isinstance(k, str) and k for k in keywords
        ):
            errors.append(f"{CATALOG}: plugin {pname} keywords must be strings")
        skills = plugin.get("skills")
        if not isinstance(skills, list) or skills != sorted(set(skills)):
            errors.append(
                f"{CATALOG}: plugin {pname} skills must be a sorted list without duplicates"
            )
            skills = []
        for skill in skills:
            if skill in seen_skills:
                errors.append(
                    f"{CATALOG}: skill {skill} is in plugins {seen_skills[skill]} and {pname}; "
                    "a skill belongs to exactly one plugin"
                )
            seen_skills[skill] = pname
    if errors:
        raise CatalogError("\n".join(errors))
    return catalog


def check_skill_name(name: str) -> list[str]:
    errors = []
    if not 1 <= len(name) <= 64 or not NAME_PATTERN.fullmatch(name):
        errors.append(
            f"skill name {name!r} must be 1 to 64 lowercase letters, digits and single hyphens"
        )
    for word in GENERIC_WORDS:
        if name == word or name.endswith("-" + word):
            errors.append(
                f"skill name {name!r} must not be or end with the generic word {word!r}"
            )
    return errors


def check_skill(root: Path, plugin: str, name: str) -> list[str]:
    directory = root / "plugins" / plugin / "skills" / name
    where = directory.relative_to(root).as_posix()
    errors = [f"{where}: {message}" for message in check_skill_name(name)]
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        return errors + [f"{where}: SKILL.md is missing"]
    text = skill_file.read_text(encoding="utf-8")
    try:
        meta = frontmatter(text)
    except ValueError as exc:
        return errors + [f"{where}/SKILL.md: {exc}"]
    if meta.get("name") != name:
        errors.append(
            f"{where}/SKILL.md: frontmatter name {meta.get('name')!r} must be {name!r}"
        )
    description = meta.get("description")
    if not isinstance(description, str) or not 1 <= len(description) <= MAX_DESCRIPTION:
        errors.append(
            f"{where}/SKILL.md: description must be 1 to {MAX_DESCRIPTION} characters"
        )
    user_invoked = meta.get("disable-model-invocation") is True
    openai = directory / "agents" / "openai.yaml"
    implicit = True
    if openai.is_file():
        policy = (
            parse_simple_yaml(openai.read_text(encoding="utf-8")).get("policy") or {}
        )
        implicit = policy.get("allow_implicit_invocation", True) is not False
    if user_invoked and implicit:
        errors.append(
            f"{where}: disable-model-invocation is true, so agents/openai.yaml must set "
            "policy.allow_implicit_invocation: false"
        )
    if not user_invoked and not implicit:
        errors.append(
            f"{where}: agents/openai.yaml disables implicit invocation, so SKILL.md must set "
            "disable-model-invocation: true"
        )
    for path in sorted(directory.rglob("*.md")):
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if PARENT_LINK.search(line):
                errors.append(
                    f"{path.relative_to(root).as_posix()}:{number}: links outside the skill with ../; "
                    "reach another skill by name"
                )
    return errors


def check_layout(root: Path, catalog: dict) -> list[str]:
    errors: list[str] = []
    declared = {plugin["name"] for plugin in catalog["plugins"]}
    plugins_dir = root / "plugins"
    present = (
        {p.name for p in plugins_dir.iterdir() if p.is_dir()}
        if plugins_dir.is_dir()
        else set()
    )
    for extra in sorted(present - declared):
        errors.append(f"plugins/{extra}: plugin directory is not in {CATALOG}")
    for plugin in catalog["plugins"]:
        skills_dir = plugins_dir / plugin["name"] / "skills"
        on_disk = (
            {p.name for p in skills_dir.iterdir() if p.is_dir()}
            if skills_dir.is_dir()
            else set()
        )
        listed = set(plugin["skills"])
        for name in sorted(on_disk - listed):
            errors.append(
                f"plugins/{plugin['name']}/skills/{name}: not listed in {CATALOG}"
            )
        for name in sorted(listed - on_disk):
            errors.append(
                f"{CATALOG}: skill {name} has no directory in plugins/{plugin['name']}/skills"
            )
        for name in sorted(listed & on_disk):
            errors.extend(check_skill(root, plugin["name"], name))
    return errors


def outputs(catalog: dict) -> dict[str, str]:
    market = catalog["marketplace"]
    version = catalog["version"]
    author = {"name": market["owner"]["name"]}
    if market["owner"].get("url"):
        author["url"] = market["owner"]["url"]
    files: dict[str, str] = {}
    files[".claude-plugin/marketplace.json"] = dump(
        {
            "name": market["name"],
            "owner": author,
            "metadata": {"description": market["description"], "version": version},
            "plugins": [
                {
                    "name": plugin["name"],
                    "source": f"./plugins/{plugin['name']}",
                    "description": plugin["description"],
                    "category": plugin["category"],
                }
                for plugin in catalog["plugins"]
            ],
        }
    )
    files[".agents/plugins/marketplace.json"] = dump(
        {
            "name": market["name"],
            "interface": {"displayName": market["displayName"]},
            "plugins": [
                {
                    "name": plugin["name"],
                    "source": {
                        "source": "local",
                        "path": f"./plugins/{plugin['name']}",
                    },
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": plugin["category"],
                }
                for plugin in catalog["plugins"]
            ],
        }
    )
    for plugin in catalog["plugins"]:
        manifest = {
            "name": plugin["name"],
            "version": version,
            "description": plugin["description"],
            "author": author,
            "homepage": REPOSITORY_URL,
            "repository": REPOSITORY_URL,
            "license": LICENSE,
            "keywords": plugin.get("keywords", []),
        }
        base = f"plugins/{plugin['name']}"
        files[f"{base}/plugin.json"] = dump(
            {"$schema": AGENT_PLUGINS_SCHEMA, **manifest}
        )
        files[f"{base}/.claude-plugin/plugin.json"] = dump(manifest)
    return files


def run(root: Path, check: bool) -> int:
    try:
        catalog = load_catalog(root)
    except CatalogError as exc:
        print(exc, file=sys.stderr)
        return 1
    errors = check_layout(root, catalog)
    expected = outputs(catalog)
    stale = []
    for relative, content in expected.items():
        path = root / relative
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            continue
        if check:
            stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"wrote {relative}")
    for relative in stale:
        errors.append(
            f"{relative}: differs from {CATALOG}; run python3 scripts/catalog.py"
        )
    for message in errors:
        print(message, file=sys.stderr)
    if not errors and check:
        print(f"{len(expected)} manifests match {CATALOG}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate and check the plugin manifests from catalog.json."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and rule violations; write nothing",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    return run(arguments.root.resolve(), arguments.check)


if __name__ == "__main__":
    raise SystemExit(main())
