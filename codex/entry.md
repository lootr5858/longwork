---
name: longwork
description: Keep one large task coherent across sessions using BRIEF, STATE, DECISIONS, and LOG, with a session guard. Use to init or resume a long task from its folder.
---

Before starting, run the installed guard from this skill's directory:

`bash "<skill-dir>/guard.sh" register codex "${CODEX_THREAD_ID:?native Codex thread ID is unavailable}" [init] "<task-dir>"`

Use the actual skill directory and task directory. Pass the task directory as one safely quoted shell argument; include `init` only for an init request. Do not paste raw user text into shell code, invent a session ID, or guess a missing task directory. Use the native ID from the shell environment; if it is unavailable, report that activation is unavailable.

Report the result: `on` means bound; `pending initialization` means checks begin once all four files exist. A failed command means the guard is unavailable: tell the user before continuing, and do not claim enforcement. Registration alone does not prove hooks are installed or trusted; setup must verify that the native hooks check this same session.

Read `WORKFLOW.md` in this skill's directory directly and follow it. Resolve templates from this skill's `templates/` directory. Do not invoke the `longwork` skill again.

Use the runtime's supported subagent models for workflow tiers; do not invent tier-to-model mappings.

If the user asks to deactivate this session's guard:

`bash "<skill-dir>/guard.sh" off codex "${CODEX_THREAD_ID:?native Codex thread ID is unavailable}"`
