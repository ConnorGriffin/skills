#!/bin/sh
# Reindex one maintained checkout in fast mode after a commit.

set -u

BIN="${CODEBASE_MEMORY_BIN:-$(command -v codebase-memory-mcp 2>/dev/null || true)}"
[ -n "$BIN" ] && [ -x "$BIN" ] || exit 0

ROOT="$(unset GIT_DIR GIT_WORK_TREE; cd "$PWD" && git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$ROOT" ] || exit 0

PAYLOAD="$(python3 -c \
  'import json,sys; print(json.dumps({"repo_path": sys.argv[1], "mode": "fast"}))' \
  "$ROOT")" || exit 0

nohup "$BIN" cli index_repository "$PAYLOAD" \
  >/dev/null 2>&1 </dev/null &
