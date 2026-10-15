#!/bin/bash
# longwork guard for Claude Code. Active only in sessions that invoked /longwork-cc.
#   guard.sh register <session_id> [init] <task-dir>   (skill invocation) bind session → task dir
#   guard.sh mark                                       (UserPromptSubmit) fingerprint task files at turn start
#   guard.sh check                                      (Stop) block once if the task files did not change this turn
#   guard.sh off <session_id>                           unbind
S="${TMPDIR:-/tmp}/longwork"
fp() { cat "$1"/BRIEF.md "$1"/STATE.md "$1"/DECISIONS.md "$1"/LOG.md 2>/dev/null | cksum; }

case "$1" in
  register)
    sid=$2; shift 2
    [ "$1" = init ] && { init=1; shift; }
    # Path as typed: drop surrounding quotes/backticks and whitespace.
    p=$(printf '%s' "$*" | tr -d '`"'"'" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    [ -n "$sid" ] && [ -n "$p" ] || { echo "longwork guard: not set (need a task dir)"; exit 0; }
    [ -n "$init" ] && mkdir -p "$p"
    d=$(cd "$p" 2>/dev/null && pwd) || { echo "longwork guard: not set ($p not found)"; exit 0; }
    mkdir -p "$S" && echo "$d" > "$S/$sid" && fp "$d" > "$S/$sid.mark"
    echo "longwork guard: on for $d" ;;
  off)
    rm -f "$S/$2" "$S/$2.mark"; echo "longwork guard: off" ;;
  mark|check)
    in=$(cat)
    sid=$(jq -r '.session_id // empty' <<<"$in")
    [ -n "$sid" ] && [ -f "$S/$sid" ] || exit 0
    d=$(cat "$S/$sid")
    if [ "$1" = mark ]; then fp "$d" > "$S/$sid.mark"; exit 0; fi
    [ "$(jq -r '.stop_hook_active // false' <<<"$in")" = true ] && exit 0
    [ -f "$d/STATE.md" ] || exit 0
    if [ "$(fp "$d")" = "$(cat "$S/$sid.mark" 2>/dev/null)" ]; then
      jq -n --arg d "$d" '{decision:"block", reason:("longwork: task files in " + $d + " unchanged this turn. Update STATE (Next, changes) and DECISIONS (any user input); if nothing changed, add one LOG line. Then end the turn.")}'
    fi ;;
esac
exit 0
