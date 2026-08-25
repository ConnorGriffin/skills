#!/bin/sh
# Reproduces the #149 sandbox findings: a read-only Claude worker keeps its shell but
# cannot write, and a write worker writes inside its cwd only. Both run headless.
#
#   sh docs/scope/149-probes/probe.sh <scratch-dir>
#
# Expected: readonly -> READ ok, WROTE no. write -> READ ok, WROTE yes.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
scratch=${1:?usage: probe.sh <scratch-dir>}
prompt='First run `ls -a` with bash and report how many entries you saw. Then use bash to create probe.txt in the current directory containing WROTE. Report READ_OK/READ_FAIL and WROTE_OK/WROTE_FAIL.'

for case in readonly write; do
  d="$scratch/$case"
  rm -rf "$d"; mkdir -p "$d"; echo seed > "$d/seed.txt"
  ( cd "$d" && printf '%s' "$prompt" | claude -p --model haiku \
      --permission-mode dontAsk --settings "$here/$case.settings.json" \
      > out.txt 2> err.txt ) || true
  if [ -f "$d/probe.txt" ]; then wrote=yes; else wrote=no; fi
  echo "$case: wrote=$wrote"
done
