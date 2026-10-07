# Agent instructions: z-shell/agent-skills

Organization policy is owned by [`z-shell/.github` `AGENTS.md`](https://github.com/z-shell/.github/blob/main/AGENTS.md). Read it before non-trivial work. This file covers only what is specific to this repository.

## Layout and ownership

- [ADR-0037](https://github.com/z-shell/.github/blob/main/decisions/0037-publish-agent-skills-from-a-dedicated-repository.md) decides this repository's layout, install routes and move order.
- `catalog.json` is the only hand-edited package metadata. Never edit a generated manifest (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `plugins/*/plugin.json`, `plugins/*/.claude-plugin/plugin.json`); change the catalog and run `python3 scripts/catalog.py`.
- Each skill lives in exactly one plugin, as real files under `plugins/<plugin>/skills/<name>/`. Drafts stay in `in-progress/`, outside every manifest.
- Name and scope skills by the organization's [skill naming and scope rules](https://github.com/z-shell/.github/blob/main/knowledge/domains/agents/skill-naming.md). A skill reaches another skill by name, never through a `../` path.
- A user-invoked skill sets `disable-model-invocation: true` in `SKILL.md` and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`; a model-invoked skill sets neither.
- `.github/skills/code-review/` is the organization's vendored review skill at its approved revision. Do not edit it here.

## Before handing off

```bash
python3 scripts/catalog.py --check
python3 -m unittest discover -s scripts -p 'test_*.py'
claude plugin validate . --strict
claude plugin validate plugins/z-shell --strict
```

A release bumps the `catalog.json` version, because Claude Code refreshes an installed plugin only when its version changes.
