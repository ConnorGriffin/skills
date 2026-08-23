#!/bin/sh
# Reindex the checkout that fired a managed Git hook.

set -u

BIN="${CODEBASE_MEMORY_BIN:-$(command -v codebase-memory-mcp 2>/dev/null || true)}"
[ -n "$BIN" ] && [ -x "$BIN" ] || {
  printf '%s\n' "Codebase Memory refresh skipped: binary is not executable" >&2
  exit 0
}
LAUNCHER="$(command -v nohup 2>/dev/null || true)"
[ -n "$LAUNCHER" ] && [ -x "$LAUNCHER" ] || {
  printf '%s\n' "Codebase Memory refresh skipped: detached launcher is unavailable" >&2
  exit 0
}

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
LIFECYCLE="$SCRIPT_DIR/cbm-lifecycle.py"

ROOT="$(unset GIT_DIR GIT_WORK_TREE; cd "$PWD" && git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$ROOT" ] || exit 0

GIT_DIR_ABS="$(unset GIT_DIR GIT_WORK_TREE; cd "$PWD" && git rev-parse --absolute-git-dir 2>/dev/null || true)"
COMMON_DIR="$(unset GIT_DIR GIT_WORK_TREE; cd "$PWD" && git rev-parse --git-common-dir 2>/dev/null || true)"
case "$COMMON_DIR" in
  /*) : ;;
  *) COMMON_DIR="$(unset GIT_DIR GIT_WORK_TREE; cd "$PWD/$COMMON_DIR" 2>/dev/null && pwd -P || true)" ;;
esac
[ -n "$GIT_DIR_ABS" ] && [ -n "$COMMON_DIR" ] || {
  printf '%s\n' "Codebase Memory refresh skipped: checkout classification failed" >&2
  exit 0
}

if [ "$GIT_DIR_ABS" != "$COMMON_DIR" ]; then
  VERSION_TMP="$(mktemp 2>/dev/null || true)"
  if [ -z "$VERSION_TMP" ] ||
    ! "$BIN" --version >"$VERSION_TMP" 2>/dev/null ||
    ! python3 "$LIFECYCLE" version "$VERSION_TMP" >/dev/null 2>&1; then
    [ -z "$VERSION_TMP" ] || rm -f "$VERSION_TMP"
    printf '%s\n' "Codebase Memory refresh skipped: binary version is unsupported" >&2
    exit 0
  fi
  rm -f "$VERSION_TMP"
  IDENTITY="$(unset GIT_DIR GIT_WORK_TREE; python3 "$LIFECYCLE" identity "$ROOT" 2>/dev/null || true)"
  PROJECT="$(printf '%s' "$IDENTITY" | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["project"])' 2>/dev/null || true)"
  [ -n "$PROJECT" ] || {
    printf '%s\n' "Codebase Memory refresh skipped: worktree identity could not be derived" >&2
    exit 0
  }
  "$LAUNCHER" "$BIN" cli --json index_repository \
    --repo-path "$ROOT" --mode fast --name "$PROJECT" \
    >/dev/null 2>&1 </dev/null &
  exit 0
fi

PAYLOAD="$(python3 -c \
  'import json,sys; print(json.dumps({"repo_path": sys.argv[1], "mode": "fast"}))' \
  "$ROOT")" || exit 0

"$LAUNCHER" "$BIN" cli index_repository "$PAYLOAD" \
  >/dev/null 2>&1 </dev/null &

exit 0
