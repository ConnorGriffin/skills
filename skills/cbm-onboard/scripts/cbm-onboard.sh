#!/bin/sh
# Register a repository with codebase-memory-mcp without clobbering local rules.

set -eu

BIN="${CODEBASE_MEMORY_BIN:-$(command -v codebase-memory-mcp 2>/dev/null || true)}"
[ -n "$BIN" ] && [ -x "$BIN" ] || {
  printf '%s\n' "codebase-memory-mcp is not executable; install it or set CODEBASE_MEMORY_BIN" >&2
  exit 1
}

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
REINDEX="$SCRIPT_DIR/cbm-reindex.sh"
TARGET="${1:-.}"
ROOT="$(git -C "$TARGET" worktree list --porcelain 2>/dev/null |
  awk '/^worktree / { print substr($0, 10); exit }')"
[ -n "$ROOT" ] || {
  printf 'not a Git repository: %s\n' "$TARGET" >&2
  exit 1
}

IGNORE="$ROOT/.cbmignore"
HOOK_PATH="$(git -C "$ROOT" rev-parse --git-path hooks/post-commit)"
case "$HOOK_PATH" in
  /*) HOOK="$HOOK_PATH" ;;
  *) HOOK="$ROOT/$HOOK_PATH" ;;
esac

[ ! -L "$IGNORE" ] || {
  printf 'refusing symlink target: %s\n' "$IGNORE" >&2
  exit 1
}
[ ! -L "$HOOK" ] || {
  printf 'refusing symlink target: %s\n' "$HOOK" >&2
  exit 1
}

BEGIN_IGNORE="# >>> cbm-onboard managed baseline — do not edit inside this block >>>"
END_IGNORE="# <<< cbm-onboard managed baseline <<<"
BEGIN_HOOK="# >>> cbm-onboard managed reindex >>>"
END_HOOK="# <<< cbm-onboard managed reindex <<<"
MANAGED_TMP="$(mktemp)"
OUTPUT_TMP="$(mktemp)"
HOOK_TMP="$(mktemp)"
trap 'rm -f "$MANAGED_TMP" "$OUTPUT_TMP" "$HOOK_TMP"' EXIT

{
  printf '%s\n' "$BEGIN_IGNORE"
  printf '%s\n' \
    ".venv/" "venv/" "env/" "__pycache__/" "*.pyc" \
    ".pytest_cache/" ".mypy_cache/" ".ruff_cache/" ".tox/" \
    "node_modules/" "dist/" "build/" "*.egg-info/" \
    ".agentflow/" ".claude/worktrees/" ".codex/worktrees/" \
    "*.db" "*.sqlite" "*.sqlite3" "*.csv" "*.parquet" \
    ".env" ".env.*" "*.pem" "*.key" "*.p12" "*.pfx" \
    ".aws/" ".ssh/" ".secrets/" "secrets/" "credentials/" "*.log"
  printf '%s\n' "$END_IGNORE"
} >"$MANAGED_TMP"

EXISTING="/dev/null"
[ -e "$IGNORE" ] && EXISTING="$IGNORE"

awk -v begin="$BEGIN_IGNORE" -v end="$END_IGNORE" '
  function rtrim(s) { sub(/[ \t]+$/, "", s); return s }
  FNR == NR { managed[FNR] = $0; managed_set[$0] = 1; managed_n = FNR; next }
  { lines[++n] = $0 }
  END {
    for (i = 1; i <= managed_n; i++) print managed[i]
    custom_n = 0
    i = 1
    while (i <= n) {
      if (rtrim(lines[i]) == begin) {
        found = 0
        for (j = i + 1; j <= n; j++) {
          if (rtrim(lines[j]) == begin) { break }
          if (rtrim(lines[j]) == end) { found = j; break }
        }
        if (found) { i = found + 1; continue }
        custom[++custom_n] = lines[i]
        i++; continue
      }
      if (rtrim(lines[i]) == end) {
        custom[++custom_n] = lines[i]
        i++; continue
      }
      if (lines[i] in managed_set) { i++; continue }
      custom[++custom_n] = lines[i]
      i++
    }
    first = 1
    last = custom_n
    while (first <= last && custom[first] == "") first++
    while (last >= first && custom[last] == "") last--
    if (last >= first) {
      print ""
      for (i = first; i <= last; i++) print custom[i]
    }
  }
' "$MANAGED_TMP" "$EXISTING" >"$OUTPUT_TMP"

if [ ! -e "$IGNORE" ] || ! cmp -s "$OUTPUT_TMP" "$IGNORE"; then
  cp "$OUTPUT_TMP" "$IGNORE"
  printf '%s\n' "updated $IGNORE"
else
  printf '%s\n' "$IGNORE is already current"
fi

mkdir -p "$(dirname "$HOOK")"
INSTALL_HOOK=1
if [ -e "$HOOK" ]; then
  FIRST_LINE="$(sed -n '1p' "$HOOK")"
  if ! printf '%s\n' "$FIRST_LINE" |
    grep -Eq '^#!.*[/[:space:]](ba|da|k|z)?sh([[:space:]]|$)'; then
    printf 'SKIP hook installation: existing hook is not a shell script; left unchanged: %s\n' \
      "$HOOK" >&2
    INSTALL_HOOK=0
  fi
else
  printf '%s\n' "#!/bin/sh" >"$HOOK_TMP"
fi

if [ "$INSTALL_HOOK" -eq 1 ]; then
  if [ -e "$HOOK" ]; then
    awk -v begin="$BEGIN_HOOK" -v end="$END_HOOK" '
      { lines[++n] = $0 }
      END {
        i = 1
        while (i <= n) {
          if (lines[i] == begin) {
            found = 0
            for (j = i + 1; j <= n; j++) {
              if (lines[j] == begin) { break }
              if (lines[j] == end) { found = j; break }
            }
            if (found) {
              if (out_n > 0 && output[out_n] == "") out_n--
              i = found + 1
              continue
            }
          }
          output[++out_n] = lines[i]
          i++
        }
        for (i = 1; i <= out_n; i++) print output[i]
      }
    ' "$HOOK" >"$HOOK_TMP"
  fi
  {
    printf '\n%s\n' "$BEGIN_HOOK"
    printf '"%s" "%s"\n' "$REINDEX" "$ROOT"
    printf '%s\n' "$END_HOOK"
  } >>"$HOOK_TMP"
  cp "$HOOK_TMP" "$HOOK"
  chmod +x "$HOOK"
  printf '%s\n' "installed managed reindex command in $HOOK"
fi

PAYLOAD="$(python3 -c \
  'import json,sys; print(json.dumps({"repo_path": sys.argv[1], "mode": "full"}))' \
  "$ROOT")"
"$BIN" cli index_repository "$PAYLOAD"
printf '%s\n' "indexed $ROOT"
