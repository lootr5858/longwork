# Longwork: one-time local setup

This folder is itself the `longwork` skill for both agents. Its `SKILL.md` is a
combined entry: Claude-only frontmatter (hooks, manual invocation) plus one
section per agent. Both sections read [WORKFLOW.md](WORKFLOW.md) and run the same
guard. [`agents/openai.yaml`](agents/openai.yaml) disables Codex implicit
invocation, matching Claude's `disable-model-invocation`.

Requirements: a local Unix environment (Linux, macOS, or WSL), Bash, `jq`, and
standard Unix utilities. Native Windows and cloud orchestration are not covered.
The task directory must be writable by the agent. The default guard store is
`/tmp/longwork-<uid>/<agent>/`, independent of the shell's `TMPDIR`. A reboot or
temporary-file cleanup removes bindings; invoke longwork again to register.
For a different store, set `LONGWORK_GUARD_DIR` identically for native hooks and
agent shell tools. A sandbox must permit writing that store.

## Install

Make this folder reachable as `longwork` in each agent's skill directory. If a
skill directory is already a symlink to this folder's parent (for example
`~/.claude/skills` and `~/.agents/skills` both pointing at the folder that holds
`longwork/`), nothing more is needed. Otherwise link the folder itself:

```bash
longwork_source=/path/to/longwork   # your longwork clone
mkdir -p "$HOME/.claude/skills" "$HOME/.agents/skills"
ln -s "$longwork_source" "$HOME/.claude/skills/longwork"
ln -s "$longwork_source" "$HOME/.agents/skills/longwork"
```

If `longwork` is already installed under another layout, move that installation
outside skill discovery first: clients can expose duplicate names instead of
merging them. Keep the source folder at its location; the hook commands use
absolute paths.

### Claude Code

The entry registers skill-scoped `UserPromptSubmit` and `Stop` hooks. It passes
Claude's `${CLAUDE_SESSION_ID}` to registration. Reload skills or restart if
needed, then invoke `/longwork [init] "<task-dir>"`. In that session, `/hooks`
should show the two guard commands. No separate `/longwork-cc` invocation.

The hook commands target `$HOME/.claude/skills/longwork/guard.sh`. If you use a
nondefault Claude skills directory, adjust the two commands in `SKILL.md`.

### Codex

Codex reads `name` and `description`; its handling of the extra Claude
frontmatter is not documented, so confirm `longwork` appears in `/skills`.

Merge the two event groups from [`codex/hooks.json`](codex/hooks.json) into
`${CODEX_HOME:-$HOME/.codex}/hooks.json`, or configure their equivalent in
`config.toml`. Preserve existing hooks and other settings. Include each guard
command once; do not install the same hooks in both JSON and TOML. If no hooks
file exists, the supplied JSON can be used as that file. Adjust command paths
if the entry is installed outside `$HOME/.agents/skills/longwork`.

Review and trust the hooks using `/hooks`; check that hooks are enabled and
restart the client if needed. Changed hook definitions require trust review
again. Invoke `$longwork [init] "<task-dir>"` or select `longwork` in `/skills`.
The name is the same as Claude's; the native invocation syntax differs.

The entry's Codex section uses the native `CODEX_THREAD_ID` supplied to shell tools.
Its availability was confirmed in the development session; the end-to-end
setup check below must verify that native hook `session_id` reaches the same
registration. If that variable is absent, activation fails visibly rather than
inventing an ID. Registration does not install, enable, or trust hooks.

## Verify once after installation

Use a disposable task folder and a fresh agent session:

1. Confirm Bash and `jq` are available, and the installed entry, guard, workflow,
   and templates are readable.
2. Invoke `longwork init <task-dir>`. Expect `pending initialization` while the
   init interview is incomplete. Follow the ordinary init/BRIEF approval flow;
   guard checks begin once all four records exist. An existing complete task
   should register as `on` immediately.
3. On a later turn, ask the agent to leave all four records unchanged for this
   disposable guard test. Verify native Stop feedback requests an update. Have
   the agent append a LOG line and finish; the repaired check should pass. This
   proves that registration and the native hook use the same session identity.
4. Repeat while deliberately making no repair. Expect one continuation, then
   an `unresolved after continuation` warning, without another guard retry.
5. Ask the agent to deactivate this session's guard using the `off` command in
   its `SKILL.md` section. Confirm a subsequent unchanged turn receives no guard feedback.
6. In a separate session that never invokes longwork, confirm the global Codex
   hooks remain silent. Verify both typed and picker-based invocation if used.

`on` confirms that binding was saved, not that native hooks ran. Hook errors,
disabled/untrusted hooks, or unsupported clients mean enforcement is unavailable.
The guard detects record changes, not their accuracy, approval compliance, or
the correctness of the task's output. It deliberately permits init interview
turns before all four records exist and warns rather than retrying indefinitely.

## Migration and validation

Move the old `longwork-cc` installation outside skill discovery; remove only
its old guard commands if they were also added to global settings. End the old
session so its registered skill hooks no longer run. Existing task files stay
valid. When an older BRIEF names `/longwork-cc`, use `longwork` to resume; propose
any BRIEF wording change through the existing BRIEF approval procedure.

Source-level checks (no live agent settings changed):

```bash
bash -n /path/to/longwork/guard.sh
python3 /path/to/longwork/tests/test_guard.py
```

These exercise hook payloads and commands in temporary installations; they do
not prove live agent hook execution. Run the native setup check after install.

Official references: [Claude skills](https://code.claude.com/docs/en/skills),
[Claude hooks](https://code.claude.com/docs/en/hooks),
[Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Codex hooks](https://learn.chatgpt.com/docs/hooks).
