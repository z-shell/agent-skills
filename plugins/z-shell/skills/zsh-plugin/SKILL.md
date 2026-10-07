---
name: zsh-plugin
description: Zsh plugins under the Z-Shell Zsh Plugin Standard 2. Use when creating a new Zsh plugin or plugin skeleton, or when maintaining an existing one, including bringing it to Standard 2, adding or changing functions, completions, configuration or unload, and wiring ZUnit and zsh-lint CI. Writing the ZUnit tests themselves belongs to zunit; a read-only compliance review belongs to the zsh-plugin-reviewer agent in z-shell/.github.
---

# Create and maintain Zsh plugins

Work against the canonical Zsh standard and the owning repository's local
contract. The skill supplies plugin-specific procedure, not independent Zsh
semantics.

## Establish the contract

Before creating or changing a plugin:

1. Read the canonical standards in `z-shell/.github` first: the Zsh standard,
   [`.github/instructions/zsh/scripting.instructions.md`](https://github.com/z-shell/.github/blob/main/.github/instructions/zsh/scripting.instructions.md),
   its policy,
   [`knowledge/domains/zsh/data/zsh-standard-policy.json`](https://github.com/z-shell/.github/blob/main/knowledge/domains/zsh/data/zsh-standard-policy.json),
   and the [Zsh Plugin Standard](https://wiki.zshell.dev/community/zsh_plugin_standard).
2. Read root `AGENTS.md` and the owning repository's local `AGENTS.md` when
   present.
3. Identify the repository compatibility floor.
4. Select `sourced-library` for the plugin entry point and
   `autoload-function` for files beneath `functions/`.

## Create a plugin

1. **Gather inputs** (ask only if not supplied):
   - An explicit target repository root. The caller must supply it; do not infer
     or default to a multi-repository checkout path.
   - Plugin name in kebab-case, for example `zsh-foo` with entry file
     `zsh-foo.plugin.zsh`.
   - One portable ASCII project identifier, for example `zsh_foo`. This owns
     every persistent public and private shell name and the
     `:zsh_foo:config` style context.

2. **Create the layout**. Create only the authoritative entrypoint initially.
   Add each optional directory only when its execution role is required:

   ```text
     <target-repository-root>/
     <name>.plugin.zsh
     lib/          # optional private eager sources
     functions/    # optional autoload functions
     completions/  # optional native completion functions
     bin/          # optional user-invoked executables
   ```

3. **Write the entry file** from `templates/template.plugin.zsh` in this skill,
   a copy of the canonical
   `knowledge/domains/plugins/templates/template.plugin.zsh` in `z-shell/.github`,
   replacing `__IDENTIFIER__` with the ASCII project identifier. Keep the
   modelines as the first two lines verbatim. Do not create shared `Plugins`
   state, scattered public configuration parameters, or a second legacy
   namespace. Add manager-specific behavior only when the user requests and
   identifies that optional profile, and keep it outside the portable contract.

4. **Write autoload function bodies**: begin each generated function body with
   `builtin emulate -L zsh`. Select only the correctness-affecting options that
   function needs. Apply `zsh/autoload/initialize`, `zsh/options/localize`, and
   the repository compatibility floor; do not copy a universal option bundle.

5. **Verify syntax and lifecycle** as described under
   [Verify every change](#verify-every-change).

6. **Report** the created tree, execution profiles, syntax result, lifecycle
   result, and any repository-floor decision.

## Maintain an existing plugin

Read the plugin's entry file, `functions/`, `completions/`, documented
configuration, unload function and tests before changing anything. List every
side effect the plugin performs at load time; that list is what unload must
reverse.

### Bring a plugin to Standard 2

Version 2 is one clean portable contract. A refactored plugin does not keep an
older namespace, shared registry, configuration parameter or directory
convention as a compatibility path.

1. Choose the one portable ASCII project identifier if the plugin has none, and
   rename every persistent shell-visible name to derive from it, with a leading
   underscore for private state and callbacks.
2. Replace configuration globals and environment variables with the project's
   `zstyle` context, and document each style.
3. Remove reads and writes of shared manager or plugin state such as a global
   `Plugins` parameter. Keep manager-specific behavior in an optional profile
   only when the user names it.
4. Make the entry file preserve caller state under
   `zsh/sourced/preserve-caller-state`, using the template's loader shape.
5. Write or complete `<identifier>_plugin_unload` so it reverses every owned
   side effect and self-destructs.
6. Record the change for users: renamed functions, styles and removed
   parameters belong in the release notes and README.

### Add or change functions

- Put a public function in `functions/` as an autoload function named from the
  identifier, beginning with `builtin emulate -L zsh`. Keep setup-only helpers
  local to the loader.
- Add the plugin's own resolved `functions/` directory to `fpath` only after
  checking that the exact path is absent, under `zsh/security/trust-paths`, and
  remove exactly that entry on unload.
- Document each new public function as part of the load surface under
  `zsh/plugin/document-load-surface`.

### Add or change completions

- Put each native completion in `completions/` as a file named `_<command>`.
  Add the directory to `fpath` the same way as `functions/`, before completion
  initialization.
- Do not run `compinit` during loading, and never `compinit -u`; the user's
  configuration, framework or manager owns completion initialization. If a
  feature needs completion after `compinit` has already run, document the
  integration step.

### Change configuration

- Read scalars with `zstyle -s`, arrays with `zstyle -a` and booleans with
  `zstyle -t` from the project context. Supply defaults as local lookup
  fallbacks; do not register them in the global style database.
- Document each new style in the README: default, value type, accepted values,
  and when it is read.

### Keep unload exact

Every new side effect needs a matching reversal in `<identifier>_plugin_unload`
under `zsh/plugin/exact-lifecycle`: remove only what the plugin owns, restore
pre-load state only while the plugin's value is still installed, and preserve
the user's newer state. Unload ends by removing itself.

### Wire CI

- **ZUnit**: add or extend `.zunit` tests under `tests/` with the `zunit` skill,
  and run them in CI. Pin ZUnit only to an exact commit from a published release.
- **zsh-lint**: call the organization reusable workflow
  `z-shell/.github/.github/workflows/zsh-lint.yml` as a job with
  `contents: read`, passing the plugin's reviewed Zsh source roots as `paths`
  and a published analyzer release commit as `zsh-lint-ref`. Pin the workflow
  and the analyzer independently to full commit SHAs. Its contract is
  [`knowledge/domains/ci/zsh-lint-ci.md`](https://github.com/z-shell/.github/blob/main/knowledge/domains/ci/zsh-lint-ci.md).
- Keep native syntax checking (`zsh -n`) as its own step; lint does not
  replace it.

## Verify every change

- Run `zsh -f -n <name>.plugin.zsh` for native syntax validation under
  `zsh/validation/native-authority`, and the same for each changed autoload
  function.
- In an isolated shell with temporary `HOME` and `ZDOTDIR`, prime the ZUnit
  lifecycle observer, snapshot the baseline, source the entry file, and
  assert the exact documented load allowlist.
- Test repeated source, partial initialization failure, hostile caller
  options, non-interactive loading, and post-load user changes. Invoke
  `<identifier>_plugin_unload` and assert ownership-aware restoration.
- Remove the temporary directory. `zsh -f` suppresses normal RCS processing,
  but a system `zshenv` may still execute.
- Run the plugin's existing ZUnit suite and lint before reporting.

Report what changed, the execution profiles, syntax, lifecycle and test results,
and any repository-floor decision.

## Canonical links for plugin decisions

- Caller-state preservation: `zsh/sourced/preserve-caller-state`.
- Autoload body initialization: `zsh/autoload/initialize`.
- Stable namespace: `zsh/plugin/stable-namespace`.
- Coherent configuration: `zsh/plugin/coherent-configuration`.
- Documented plugin effects: `zsh/plugin/document-load-surface`.
- Owned-effect cleanup: `zsh/plugin/exact-lifecycle`.
- Controlled autoload paths: `zsh/security/trust-paths`.

Keep the rule rationale in the canonical instruction. A plugin must reverse
every owned side effect and self-destruct; syntax success alone is not a
behavioral result.
