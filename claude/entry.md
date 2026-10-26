---
name: longwork
description: Keep one large task coherent across sessions using BRIEF, STATE, DECISIONS, and LOG, with a session guard. Use to init or resume a long task from its folder.
disable-model-invocation: true
argument-hint: "[init] <task-dir>"
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/guard.sh *)
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

Before starting, run `bash "${CLAUDE_SKILL_DIR}/guard.sh" register claude "${CLAUDE_SESSION_ID}" [init] "<task-dir>"`, using the actual task directory as one safely quoted shell argument. Include `init` only for an init request. Do not paste raw arguments into shell code or guess a missing task directory.

Report the result: `on` means bound; `pending initialization` means checks begin once all four files exist. A failed command means the guard is unavailable: tell the user before continuing, and do not claim enforcement. Hook execution must be verified once during setup.

Read `${CLAUDE_SKILL_DIR}/WORKFLOW.md` directly and follow it. Resolve templates from `${CLAUDE_SKILL_DIR}/templates/`. Do not call the Skill tool with `longwork` again.

Subagent tiers: `light` → `haiku`; `standard` → `sonnet`; `deep` → inherit.

If the user asks to deactivate this session's guard: `bash "${CLAUDE_SKILL_DIR}/guard.sh" off claude "${CLAUDE_SESSION_ID}"`.
