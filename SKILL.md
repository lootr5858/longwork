---
name: longwork
description: Keep one large task coherent across sessions using BRIEF, STATE, DECISIONS, and LOG, with a session guard. Use to init or resume a long task from its folder.
disable-model-invocation: true
argument-hint: "[init] <task-dir>"
allowed-tools: Bash(bash "${CLAUDE_SKILL_DIR}/guard.sh" *)
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/longwork/guard.sh" mark claude'
  Stop:
    - hooks:
        - type: command
          command: 'bash "$HOME/.claude/skills/longwork/guard.sh" check claude'
---

Task request: $ARGUMENTS

This entry serves Claude Code and Codex. Follow only your agent's section; the other section's variables are not set for you. Then read `WORKFLOW.md` in this skill's directory (the folder holding this SKILL.md) and follow it. Resolve templates from its `templates/`. Do not invoke the `longwork` skill again.

Shared rules: run each guard command by itself, with nothing chained before or after it; pass the task directory as one safely quoted shell argument; include `init` only for an init request; never paste raw user text into shell code, invent a session ID, or guess a missing task directory. `on` means bound; `pending initialization` means checks begin once all four files exist. A failed command means the guard is unavailable: tell the user before continuing, and do not claim enforcement.

## Claude Code

- Register: `bash "${CLAUDE_SKILL_DIR}/guard.sh" register claude "${CLAUDE_SESSION_ID}" [init] "<task-dir>"`
- Subagent tiers: `light` → `haiku`; `standard` → `sonnet`; `deep` → inherit.
- Deactivate on request: `bash "${CLAUDE_SKILL_DIR}/guard.sh" off claude "${CLAUDE_SESSION_ID}"`

## Codex

- Register: `bash "<skill-dir>/guard.sh" register codex "${CODEX_THREAD_ID:?native Codex thread ID is unavailable}" [init] "<task-dir>"`. If the ID is unavailable, report that activation is unavailable.
- Registration does not prove hooks are installed or trusted; setup verifies that.
- Use the runtime's supported subagent models for tiers; do not invent mappings.
- Deactivate on request: `bash "<skill-dir>/guard.sh" off codex "${CODEX_THREAD_ID:?native Codex thread ID is unavailable}"`

## Other agents

No guard. Read WORKFLOW.md and follow it; tell the user enforcement is unavailable.
