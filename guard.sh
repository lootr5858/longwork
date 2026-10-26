#!/bin/bash
# Shared turn-update reminder for local Claude Code and Codex sessions.
# register <agent> <session-id> [init] <task-dir> | off <agent> <session-id>
# mark <agent> | check <agent>   (native hook JSON on stdin)
set -u
set -o pipefail
umask 077

fail() { printf 'longwork guard: %s\n' "$*" >&2; exit 1; }
action=${1-}
agent=${2-}
case "$agent" in claude|codex) ;; *) fail 'agent must be claude or codex' ;; esac
command -v jq >/dev/null 2>&1 || fail 'jq is required'
# Native hooks and sandboxed shell tools may have different TMPDIR values.
store="${LONGWORK_GUARD_DIR:-/tmp/longwork-$(id -u)}/$agent"

case "$action" in
  register|off) sid=${3-} ;;
  mark|check)
    [ "$#" -eq 2 ] || fail "usage: guard.sh $action <agent>"
    input=$(cat) || fail 'cannot read hook input'
    sid=$(jq -er '.session_id | select(type == "string" and length > 0)' <<<"$input") || fail 'hook input needs a session_id'
    ;;
  *) fail 'action must be register, mark, check, or off' ;;
esac
case "$sid" in ''|*[!a-zA-Z0-9_-]*) fail 'invalid session ID' ;; esac
state="$store/$sid.json"

fingerprint() {
  local file sum
  for file in BRIEF.md STATE.md DECISIONS.md LOG.md; do
    [ -f "$dir/$file" ] && [ -r "$dir/$file" ] || return 1
    sum=$(cksum < "$dir/$file") || return 1
    printf '%s %s\n' "$file" "$sum"
  done
}

save() {
  local tmp
  [ ! -d "$state" ] || fail 'guard state path is a directory'
  tmp=$(mktemp "$store/.state.XXXXXX") || fail 'cannot create guard state'
  if ! printf '%s\n' "$record" > "$tmp" || ! mv -f -- "$tmp" "$state"; then
    rm -f -- "$tmp"
    fail 'cannot save guard state'
  fi
}

if [ "$action" = off ]; then
  [ "$#" -eq 3 ] || fail 'usage: guard.sh off <agent> <session-id>'
  rm -f -- "$state" || fail 'cannot remove guard state'
  printf 'longwork guard: off\n'
  exit 0
fi

if [ "$action" = register ]; then
  shift 3
  phase=active
  if [ "${1-}" = init ]; then phase=init; shift; fi
  [ "$#" -eq 1 ] && [ -n "$1" ] || fail 'usage: guard.sh register <agent> <session-id> [init] <task-dir>'
  if [ "$phase" = init ]; then mkdir -p -- "$1" || fail 'cannot create task directory'; fi
  dir=$(cd -- "$1" 2>/dev/null && pwd -P) || fail 'task directory not found'
  if mark=$(fingerprint); then
    phase=active
  elif [ "$phase" = active ]; then
    fail 'resume requires readable BRIEF.md, STATE.md, DECISIONS.md, and LOG.md'
  else
    mark=''
  fi
  mkdir -p -- "$store" || fail 'cannot create guard storage'
  record=$(jq -n --arg dir "$dir" --arg phase "$phase" --arg mark "$mark" \
    '{dir:$dir, phase:$phase, mark:$mark, blocked:false}') || fail 'cannot encode guard state'
  save
  if [ "$phase" = init ]; then
    printf 'longwork guard: pending initialization for %s (checks begin when all four task files exist)\n' "$dir"
  else
    printf 'longwork guard: on for %s\n' "$dir"
  fi
  exit 0
fi

# Installed global hooks are silent for sessions that have not invoked longwork.
[ -e "$state" ] || exit 0
record=$(cat -- "$state") || fail 'cannot read guard state'
jq -e '(.dir | type == "string") and (.mark | type == "string") and
  (.phase == "init" or .phase == "active") and (.blocked | type == "boolean")' \
  >/dev/null <<<"$record" || fail 'invalid guard state; invoke longwork again'
dir=$(jq -r '.dir' <<<"$record")
phase=$(jq -r '.phase' <<<"$record")
blocked=$(jq -r '.blocked' <<<"$record")

if [ "$action" = mark ]; then
  # Codex may submit the Stop reason as a new prompt. Keep the original baseline
  # until the repair is checked, rather than treating it as a fresh user turn.
  [ "$blocked" = true ] && exit 0
  mark=$(fingerprint) || mark=''
  record=$(jq --arg mark "$mark" '.mark = $mark' <<<"$record") || fail 'cannot encode turn baseline'
  save
  exit 0
fi

reason=''
if [ ! -d "$dir" ]; then
  reason="task directory is unavailable: $dir"
elif current=$(fingerprint); then
  if [ "$phase" = init ]; then
    record=$(jq --arg mark "$current" '.phase = "active" | .mark = $mark | .blocked = false' <<<"$record") || fail 'cannot activate initialized task'
    save
    exit 0
  fi
  mark=$(jq -r '.mark' <<<"$record")
  if [ -z "$mark" ]; then
    reason="turn baseline is unavailable for $dir; report the guard failure and re-register"
  elif [ "$current" = "$mark" ]; then
    reason="task files in $dir are unchanged this turn. Update STATE (Next, changes) and DECISIONS (user input); if nothing changed, append one LOG line"
  fi
elif [ "$phase" = init ]; then
  # Init interviews can span turns before the workflow creates the four files.
  exit 0
else
  reason="task files in $dir are missing or unreadable; report the issue and follow longwork's issue procedure"
fi

if [ -z "$reason" ]; then
  if [ "$blocked" = true ]; then
    record=$(jq '.blocked = false' <<<"$record") || fail 'cannot finish repair check'
    save
  fi
  exit 0
fi

retry=$(jq -r '.stop_hook_active == true' <<<"$input") || fail 'invalid Stop input'
if [ "$blocked" = true ] || [ "$retry" = true ]; then
  record=$(jq '.blocked = false' <<<"$record") || fail 'cannot finish repair check'
  save
  jq -n --arg message "longwork guard: unresolved after continuation: $reason. No further automatic retry; report this limitation to the user." \
    '{systemMessage:$message}'
else
  record=$(jq '.blocked = true' <<<"$record") || fail 'cannot record repair attempt'
  save
  jq -n --arg reason "longwork: $reason. Then end the turn; if unable to repair, explain why." \
    '{decision:"block", reason:$reason}'
fi
