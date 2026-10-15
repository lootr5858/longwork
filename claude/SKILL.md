---
name: longwork-cc
description: Claude Code entry for longwork. Adds a session-only guard that keeps the task files current every turn.
disable-model-invocation: true
argument-hint: "[init] <task-dir>"
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/guard.sh *)
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/longwork-cc/guard.sh mark"
  Stop:
    - hooks:
        - type: command
          command: "$HOME/.claude/skills/longwork-cc/guard.sh check"
---

Guard status: !`${CLAUDE_SKILL_DIR}/guard.sh register ${CLAUDE_SESSION_ID} $ARGUMENTS`

If the guard status is not "on", tell the user before continuing.

Call the Skill tool with "longwork", passing `$ARGUMENTS`, and follow it.

## Subagent tiers in Claude Code

Pass the tier's model to the Agent tool:

| Tier | `model` |
|---|---|
| `light` | `haiku` |
| `standard` | `sonnet` |
| `deep` | omit (inherit) |

Aliases resolve to the newest model of each class.

To turn the guard off for this session: `${CLAUDE_SKILL_DIR}/guard.sh off ${CLAUDE_SESSION_ID}`.
