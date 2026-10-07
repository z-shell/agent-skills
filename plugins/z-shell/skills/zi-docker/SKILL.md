---
name: zi-docker
description: zd, Zi's Docker environment from z-shell/zd. Use when running Zi commands or the Zi ZUnit suite in a container or against a specific Zsh version, opening a clean shell with Zi loaded, testing a Zi revision from another repository, reproducing Linux Zsh failures, validating module ABI boundaries, or collecting controlled benchmark evidence. Not for routine syntax-only checks; writing ZUnit tests for a plugin belongs to zunit, installing Zi on the user's machine to zi-install.
---

# Zi in Docker with zd

`z-shell/zd` serves two jobs:

- It is the test harness and container environment for Zi.
- It provides controlled `runtime` and `module-build` profiles for Zsh work that does not load Zi.

Pick the section that matches the task. Read the owning repository's checks and compatibility floor first, and keep the user's workload and target versions.

## Run Zi in a container

The zd [local testing guide](https://github.com/z-shell/zd/blob/6b20914a70baa11a923c934fb45cb6b03dc09b66/docs/local-testing.md) owns the targets and variables. From a zd checkout:

- `make test` runs the Zi ZUnit suite natively, installing `zunit` on first run; `make test FILE=<suite>` runs one suite, such as `ice` or `plugins`.
- `make run CMD="<zi command>"` runs one Zi command in Docker, and `TAG=zsh-<version>` selects the Zsh version.
- `make shell` opens an interactive shell with Zi loaded.

Prebuilt images are `ghcr.io/z-shell/zd:latest` and one tag per Zsh version, such as `zsh-5.9`. Check the current tag list in the zd README rather than assuming one.

To test a Zi revision from another repository, call zd's reusable `test-native.yml` with `zi_repo` and `zi_ref`, as the [cross-repository guide](https://github.com/z-shell/zd/blob/6b20914a70baa11a923c934fb45cb6b03dc09b66/docs/cross-repo.md) shows. Pin the called workflow to a full commit SHA.

## Controlled Zsh execution

Read the organization [selection guidance](https://github.com/z-shell/.github/blob/main/.github/instructions/quality/controlled-validation.instructions.md) before choosing this route.

Choose `runtime` for source tests or `module-build` for a compiled module. Obtain an already qualified immutable image and the corresponding pinned zd runner. Inspect the runner's `--help` and [controlled-execution contract](https://github.com/z-shell/zd/blob/f8d74a1c916d42c99fea2600adff3607f67ee4bc/docs/controlled-execution.md) when preparing a run. Do not infer installed tools from a legacy zd tag.

Run the repository-owned entrypoint with a fresh output directory outside its Git source tree. Pass prepared Git fixtures as named inputs. Finish installation, cloning and image preparation before a benchmark; leave workload network access disabled. Declare required non-secret environment values explicitly. Preserve command argument boundaries instead of evaluating a command string.

Inspect `execution.json`, runtime/package identities, workload logs and raw reports. A container's zero exit status is useful only alongside the repository's observable assertions. Exercise expected failure and timeout propagation when introducing a new entrypoint or image. For performance, inspect same-run A/A noise before attributing a delta to source changes; use the existing `benchmark-report` action for ADR-0024 comparisons.

## Report

Report passed, failed and unavailable coverage separately. Retain evidence and state whether native platforms, real startup fixtures or interactive behavior remain unmeasured. The organization [zd integration runbook](https://github.com/z-shell/.github/blob/main/runbooks/zd-validation.md) owns CI setup and pilot entrypoints. This skill grants no publication or external-write authority.
