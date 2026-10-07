<div align="center">
  <a href="https://github.com/z-shell/agent-skills">
    <img
      src="https://raw.githubusercontent.com/z-shell/.github/main/profile/img/logo.svg"
      alt="Z-Shell logo"
      width="72"
      height="72"
    />
  </a>

  <h1>Z-Shell agent skills</h1>
  <p>Agent skills for Zi, Zsh plugins, ZUnit and zd, installable as a Claude Code or Codex plugin.</p>
  <p>
    <a href="https://github.com/z-shell/agent-skills/actions/workflows/ci.yml">
      <img
        src="https://github.com/z-shell/agent-skills/actions/workflows/ci.yml/badge.svg?branch=main"
        alt="CI status"
      />
    </a>
    <a href="../LICENSE">
      <img
        src="https://img.shields.io/github/license/z-shell/agent-skills"
        alt="License"
      />
    </a>
  </p>
</div>

## Features

- One `z-shell` plugin that installs from this repository as a Claude Code marketplace or a Codex repository marketplace.
- Skills named after the subject they cover (`zi-docker`, `zi-install`, `zsh-plugin`, `zunit`), following the organization's [skill naming and scope rules](https://github.com/z-shell/.github/blob/main/knowledge/domains/agents/skill-naming.md).
- One hand-edited `catalog.json`; every plugin and marketplace manifest is generated from it and checked in CI.
- Pinned copies for projects that need a skill for hosted agents, verified by the organization's approved-skill pins.

> [!NOTE]
> Skills move here from `z-shell/.github` one at a time ([z-shell/.github#741](https://github.com/z-shell/.github/issues/741)). The plugin currently ships `zi-docker`, `zsh-plugin` and `zunit`; `zi-install` follows.

## Requirements

- Claude Code with plugin support, or Codex with plugin marketplaces
- Python 3.10 or later to run the catalog generator and its tests

## Installation

Pick one route per project. A project that vendors a pinned skill should not also install the same skill from the plugin, because the agent would load it twice.

### Claude Code

```console
claude plugin marketplace add z-shell/agent-skills
claude plugin install z-shell@z-shell
```

### Codex

```console
codex plugin marketplace add z-shell/agent-skills
codex plugin add z-shell@z-shell
```

### Pinned project copy

Projects that need a skill for hosted agents keep a pinned copy under `.github/skills/`, approved in `z-shell/.github` and checked by its Org Routing workflow. See [organization review](https://github.com/z-shell/.github/blob/main/runbooks/org-review.md#install-or-update-after-authorization).

## Usage

Skills load when a task matches their description, or when invoked by name, for example `/z-shell:zunit` in Claude Code. A skill that acts on your machine, such as installing Zi, runs only when you invoke it.

## Configuration

`catalog.json` is the only hand-edited package metadata: the version, the marketplace, each plugin and its skill list.

| Generated file                                | Consumer                     |
| :-------------------------------------------- | :--------------------------- |
| `.claude-plugin/marketplace.json`             | Claude Code marketplace      |
| `.agents/plugins/marketplace.json`            | Codex repository marketplace |
| `plugins/<plugin>/plugin.json`                | Agent Plugins manifest       |
| `plugins/<plugin>/.claude-plugin/plugin.json` | Claude Code plugin manifest  |

> [!IMPORTANT]
> Every release bumps the `catalog.json` version. Claude Code refreshes an installed plugin only when its version changes.

## Lifecycle and side effects

- Installing the plugin copies its skills into the agent's plugin cache; nothing runs at install time.
- Skills carry no hooks or MCP servers.
- A skill that changes your machine or published state is user-invoked: it sets `disable-model-invocation: true` and, for Codex, `policy.allow_implicit_invocation: false`.

## Repository layout

| Path                              | Contents                                             |
| :-------------------------------- | :--------------------------------------------------- |
| `catalog.json`                    | Hand-edited package metadata                         |
| `plugins/<plugin>/skills/<name>/` | Published skills; each belongs to exactly one plugin |
| `in-progress/<name>/`             | Public drafts, outside every manifest                |
| `scripts/catalog.py`              | Manifest generator and skill rule checks             |

## Verification

From the repository root:

```bash
python3 scripts/catalog.py --check
python3 -m unittest discover -s scripts -p 'test_*.py'
claude plugin validate . --strict
claude plugin validate plugins/z-shell --strict
```

The last two commands need the `claude` CLI.

## Documentation and support

- [ADR-0037: the agent-skills repository](https://github.com/z-shell/.github/blob/main/decisions/0037-publish-agent-skills-from-a-dedicated-repository.md)
- [Skill naming and scope rules](https://github.com/z-shell/.github/blob/main/knowledge/domains/agents/skill-naming.md)
- [Z-Shell wiki](https://wiki.zshell.dev/)
- [Report an issue](https://github.com/z-shell/agent-skills/issues)

## Release model

Contributions integrate on `main` through pull requests. Releases are semantic version tags (`vMAJOR.MINOR.PATCH`) matching the `catalog.json` version; plugin installs follow the version in the generated manifests.

## Contributing and license

Contributions follow the [Z-Shell organization guidance](https://github.com/z-shell/.github). This project is distributed under the terms in <a href="../LICENSE">LICENSE</a>.

---

<div align="center">
  <p>Developed with ❤️ by the <a href="https://github.com/z-shell">Z-Shell Community</a>.</p>
</div>
