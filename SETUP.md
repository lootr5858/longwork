# Longwork: one-time local setup

Install one entry named `longwork` for each agent. Both entries read the same
workflow and run the same guard. The `claude/entry.md` and `codex/entry.md` files
are installation templates, not additional discoverable skills.

Requirements: a local Unix environment (Linux, macOS, or WSL), Bash, `jq`, and
standard Unix utilities. Native Windows and cloud orchestration are not covered.
The task directory must be writable by the agent. The default guard store is
`/tmp/longwork-<uid>/<agent>/`, independent of the shell's `TMPDIR`. A reboot or
temporary-file cleanup removes bindings; invoke longwork again to register.
For a different store, set `LONGWORK_GUARD_DIR` identically for native hooks and
agent shell tools. A sandbox must permit writing that store.

## Install entries

These commands are for **new destination directories**. If `longwork` is already
installed, move that installation outside the agent's skill discovery folders
first. Do not install both the generic root skill and an adapter with the same
name: clients can expose duplicates instead of merging them.

Keep the source folder at this location; the symlinks keep future workflow and
guard fixes shared. If the source lives elsewhere, change `longwork_source`.

### Claude Code

```bash
longwork_source=/path/to/longwork   # your longwork clone
longwork_target="$HOME/.claude/skills/longwork"
mkdir -p "$HOME/.claude/skills"
mkdir "$longwork_target" && \
  ln -s "$longwork_source/claude/entry.md" "$longwork_target/SKILL.md" && \
  ln -s "$longwork_source/SKILL.md" "$longwork_target/WORKFLOW.md" && \
  ln -s "$longwork_source/guard.sh" "$longwork_target/guard.sh" && \
  ln -s "$longwork_source/templates" "$longwork_target/templates" && \
  ln -s "$longwork_source/SETUP.md" "$longwork_target/SETUP.md"
```

The entry registers skill-scoped `UserPromptSubmit` and `Stop` hooks. It passes
Claude's `${CLAUDE_SESSION_ID}` to registration. Reload skills or restart if
needed, then invoke `/longwork [init] "<task-dir>"`. In that session, `/hooks`
should show the two guard commands. No separate `/longwork-cc` invocation.

If you use a nondefault Claude skills directory, adjust the two hook commands
in the installed entry to match. The supplied template targets the standard
`$HOME/.claude/skills/longwork` installation.

### Codex

```bash
longwork_source=/path/to/longwork   # your longwork clone
longwork_target="$HOME/.agents/skills/longwork"
mkdir -p "$HOME/.agents/skills"
mkdir "$longwork_target" && \
  ln -s "$longwork_source/codex/entry.md" "$longwork_target/SKILL.md" && \
  ln -s "$longwork_source/SKILL.md" "$longwork_target/WORKFLOW.md" && \
  ln -s "$longwork_source/guard.sh" "$longwork_target/guard.sh" && \
  ln -s "$longwork_source/templates" "$longwork_target/templates" && \
  ln -s "$longwork_source/SETUP.md" "$longwork_target/SETUP.md"
```

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

The Codex entry uses the native `CODEX_THREAD_ID` supplied to shell tools.
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
5. Ask the agent to deactivate this session's guard using its entry's `off`
   command. Confirm a subsequent unchanged turn receives no guard feedback.
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
