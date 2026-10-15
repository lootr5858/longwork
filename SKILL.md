---
name: longwork
description: Keep one large task coherent and correct across many sessions through four task files (BRIEF, STATE, DECISIONS, LOG). Use to init or resume a long task from its folder.
---

# Longwork

One task, one folder, many sessions. The files are the memory; chat history is not. Any new session continues from the files alone, losing nothing.

Invoke as `longwork init <task-dir>` or `longwork <task-dir>`. The user names the task dir. Read that folder's files and the sources BRIEF lists; reach anything else only when the user names it.

## Files

| File | Holds | At session start |
|---|---|---|
| `BRIEF.md` | objective, scope, rules, sources, files to edit with base hashes, checks, mode, done-when | read |
| `STATE.md` | Next, open issues, pending approvals, item table, current hashes | read |
| `DECISIONS.md` | the user's decisions and key inputs | read |
| `LOG.md` | append-only history | search on demand |

Skeletons: [`templates/`](templates/). Add subfolders as the task needs (`plans/`, `evidence/`, `baseline/`, `scratch/`).

### BRIEF

Stable. To change it, show the user the exact edit and wait for approval. Each rule cites the D-ID that set it.

Mode is `attended` by default: stop at every ⏸ checkpoint and every question. BRIEF may mark named steps `continuous`: stop only on an issue.

### STATE

Live state only. **Next** is one actionable line. Item rows are one line each: id · item · status · note. Statuses: `pending` · `in progress` · `⏸ waiting` · `blocked (I-xx)` · `done`.

Keep it under ~1,500 words. Past that, at the next checkpoint move resolved and historical content to LOG. Live content stays: Next, open issues, pending approvals, unfinished items.

### DECISIONS

The ledger of the user's word. Record every decision, approval, preference, correction, or fact the user gives, in the turn it is given: `D-nn`, date, the user's words (quote or tight paraphrase), scope.

Append-only. A change is a new entry marked `supersedes D-x`; set the old entry's status to `superseded by D-y`. Entries are never deleted or reworded.

**Conflict:** when new input contradicts an active entry, stop, show both side by side, and ask which holds. Record the answer as a new entry.

### LOG

Append-only, newest last. One dated paragraph per session: what was done, where it stopped. One line for a turn that changed nothing else. Resolved issues move here from STATE, keeping their I-ID.

## Init

1. Settle with the user, in rounds (use the `grilling` skill when available): objective, scope and out of scope, rules, sources, files to edit, session-start checks, mode, done-when.
2. Write the four files from the templates. Record each answer in DECISIONS.
3. Show BRIEF. Work starts after the user approves it; record the approval in DECISIONS.

## Session start

1. Read BRIEF, STATE, DECISIONS.
2. **Verify:** hash each file under BRIEF *Files to edit* and run each BRIEF check. Compare with the latest recorded value (STATE *Current hashes*, else BRIEF base). A mismatch is an issue.
3. **Report:** state, open issues, pending approvals, Next.
4. Attended: stop for the user. Continuous: continue from Next.

## During work

- Before a file's first edit in a session, re-hash it against its latest recorded value. After an approved edit, record the new hash in STATE.
- Take project facts only from BRIEF sources, the task files, or the user. When a fact is missing, stop and say exactly what is missing.
- **Issue** (mismatch, conflict, surprise, failed check): stop; record `I-nn` in STATE with symptom and evidence; find the root cause; propose fixes; act after the user approves. Record the approval in DECISIONS and the resolution in LOG.

## Every turn

Before the turn ends, the files reflect it: STATE for Next and anything that changed, DECISIONS for any user input, or one LOG line when nothing else changed.

## Subagents

Delegate read-heavy or parallel work, tagged with a tier; the platform maps tiers to models:

- `light`: search, list, extract, mechanical checks.
- `standard`: analysis, review.
- `deep`: design, correctness-critical judgement.

The prompt carries the objective, boundaries, allowed sources (paths, not pasted content), output format, and done-when. The return is ≤ ~300 words: result, evidence paths, confidence, gaps. Larger output goes to `<task-dir>/scratch/`, and only its path returns.

## Session end

At a checkpoint or phase end, never mid-item, propose a fresh session: make STATE current, then give the resume line `longwork <task-dir>`. STATE is the handoff.
