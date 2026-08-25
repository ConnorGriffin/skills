#!/bin/sh
# Executed contract for #149. Establishes, by running them, the facts the work order
# relies on. Usage:
#
#   sh docs/scope/149-probes/probe.sh <scratch-dir> > docs/scope/149-probes/output.txt 2>&1
#
# Cases:
#   readonly  - a read-only worker keeps a shell and cannot write anywhere
#   write     - a write worker writes in its cwd and is refused outside it
#               (outside = a home-directory path, not a temp path)
#   session   - a caller-supplied --session-id is honored, --resume carries context,
#               --output-format json exposes the fields the adapter parses
#   resumed   - a RESUMED read-only worker is still sandboxed (the settings file is
#               passed again on resume; this is the guarantee the pack depends on)
#
# All captured text is redacted of absolute home paths before printing: scripts/validate.py
# forbids a literal user path in any tracked file AND in all reachable history.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
scratch=${1:?usage: probe.sh <scratch-dir>}
mkdir -p "$scratch"
# The escape target must sit outside the session temp region: the sandbox documents
# the working directory AND the session temp directory as writable, so a /tmp target
# proves nothing about confinement.
outside="$HOME/.cache/149-probe-escape"
mkdir -p "$outside"

echo "# probe run $(git -C "$here" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "# claude $(claude --version 2>&1 | head -1)"

for case in readonly write; do
  d="$scratch/$case"
  rm -rf "$d"; mkdir -p "$d"; echo seed > "$d/seed.txt"
  prompt="Do these three things with bash, then report. 1) run \`ls -a\` and say how many entries. 2) create probe.txt in the current directory containing WROTE. 3) create $outside/escape-$case.txt containing ESCAPED. Report READ_OK/READ_FAIL, WROTE_OK/WROTE_FAIL, ESCAPE_OK/ESCAPE_FAIL."
  rm -f "$outside/escape-$case.txt"
  ( cd "$d" && printf '%s' "$prompt" | claude -p --model haiku --effort medium \
      --permission-mode dontAsk --settings "$here/$case.settings.json" \
      > out.txt 2> err.txt ) || true
  [ -f "$d/probe.txt" ] && cwd_write=yes || cwd_write=no
  [ -f "$outside/escape-$case.txt" ] && escaped=yes || escaped=no
  echo "$case: wrote_in_cwd=$cwd_write escaped_cwd=$escaped"
  # The worker's own report, so a dead shell is distinguishable from a blocked write.
  echo "$case: report=$(tr '\n' ' ' < "$d/out.txt" | sed "s|$HOME|\$HOME|g" | cut -c1-220)"
done
rmdir "$outside" 2>/dev/null || true

# session identity, effort passthrough, and the JSON fields the adapter parses
d="$scratch/session"; rm -rf "$d"; mkdir -p "$d"
u=$(python3 -c 'import uuid;print(uuid.uuid4())')
( cd "$d" && printf 'Reply with exactly: FIRST' | claude -p --model haiku --effort medium \
    --session-id "$u" --output-format json > first.json 2> first.err ) || true
( cd "$d" && printf 'What did you reply a moment ago? One word.' | claude -p --model haiku \
    --resume "$u" --output-format json > second.json 2> second.err ) || true
python3 - "$d" "$u" <<'PY'
import json, sys
d, u = sys.argv[1], sys.argv[2]
first = json.load(open(f"{d}/first.json"))
second = json.load(open(f"{d}/second.json"))
print("session: id_honored=%s resume_carries_context=%s" % (
    first.get("session_id") == u, "FIRST" in str(second.get("result", "")).upper()))
print("session: parsed_fields=%s" % sorted(
    k for k in ("session_id", "result", "is_error", "total_cost_usd", "permission_denials")
    if k in first))
PY

# A resumed read-only worker must still be refused a write. If resume rebuilds its
# configuration from the session record rather than the settings file, this is where
# the pack's OS-enforcement claim would fail.
d="$scratch/resumed"; rm -rf "$d"; mkdir -p "$d"
u=$(python3 -c 'import uuid;print(uuid.uuid4())')
( cd "$d" && printf 'Reply with exactly: READY' | claude -p --model haiku \
    --permission-mode dontAsk --settings "$here/readonly.settings.json" \
    --session-id "$u" --output-format json > first.json 2> first.err ) || true
( cd "$d" && printf 'Use bash to create resumed.txt in the current directory containing WROTE. Report WROTE_OK or WROTE_FAIL.' \
    | claude -p --model haiku --permission-mode dontAsk --settings "$here/readonly.settings.json" \
    --resume "$u" > second.txt 2> second.err ) || true
[ -f "$d/resumed.txt" ] && rw=yes || rw=no
echo "resumed: wrote_after_resume=$rw"
echo "resumed: report=$(tr '\n' ' ' < "$d/second.txt" | sed "s|$HOME|\$HOME|g" | cut -c1-220)"
