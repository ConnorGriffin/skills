#!/bin/sh
# Remove one ephemeral checkout's deterministic Codebase Memory project.

set -eu

BIN="${CODEBASE_MEMORY_BIN:-$(command -v codebase-memory-mcp 2>/dev/null || true)}"
[ -n "$BIN" ] && [ -x "$BIN" ] || {
  printf '%s\n' "codebase-memory-mcp is not executable; install it or set CODEBASE_MEMORY_BIN" >&2
  exit 1
}

TARGET="."
if [ "$#" -gt 1 ]; then
  printf '%s\n' "expected at most one repository path" >&2
  exit 1
fi
if [ "$#" -eq 1 ]; then
  case "$1" in
    --*)
      printf 'unknown option: %s\n' "$1" >&2
      exit 1
      ;;
    *) TARGET="$1" ;;
  esac
fi

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
LIFECYCLE="$SCRIPT_DIR/cbm-lifecycle.py"
IDENTITY_TMP="$(mktemp)"
VERSION_TMP="$(mktemp)"
RESPONSE_TMP="$(mktemp)"
trap 'rm -f "$IDENTITY_TMP" "$VERSION_TMP" "$RESPONSE_TMP"' EXIT

python3 "$LIFECYCLE" identity "$TARGET" >"$IDENTITY_TMP"
PROJECT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["project"])' "$IDENTITY_TMP")"
"$BIN" --version >"$VERSION_TMP"
python3 "$LIFECYCLE" version "$VERSION_TMP"

DELETE_EXIT=0
"$BIN" cli --json delete_project --project "$PROJECT" >"$RESPONSE_TMP" || DELETE_EXIT=$?
case "$DELETE_EXIT" in
  0)
    python3 "$LIFECYCLE" response "$PROJECT" deleted false "$RESPONSE_TMP"
    printf '%s\n' "deleted Codebase Memory project $PROJECT"
    ;;
  1)
    python3 "$LIFECYCLE" response "$PROJECT" not_found true "$RESPONSE_TMP"
    printf '%s\n' "Codebase Memory project $PROJECT was not found"
    ;;
  *)
    printf 'Codebase Memory delete failed with exit %s\n' "$DELETE_EXIT" >&2
    exit 1
    ;;
esac
