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
LIFECYCLE="$SCRIPT_DIR/cbm-lifecycle.py"

THIS_CHECKOUT=0
NO_HOOKS=0
TARGET="."
TARGET_SET=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --this-checkout) THIS_CHECKOUT=1 ;;
    --no-hooks) NO_HOOKS=1 ;;
    --*)
      printf 'unknown option: %s\n' "$1" >&2
      exit 1
      ;;
    *)
      [ "$TARGET_SET" -eq 0 ] || {
        printf '%s\n' "expected at most one repository path" >&2
        exit 1
      }
      TARGET="$1"
      TARGET_SET=1
      ;;
  esac
  shift
done

if [ "$NO_HOOKS" -eq 1 ] && [ "${CBM_SKIP_INDEX:-0}" = "1" ]; then
  printf '%s\n' "CBM_SKIP_INDEX=1 is not supported with --no-hooks" >&2
  exit 1
fi

IDENTITY_TMP="$(mktemp)"
VERSION_TMP="$(mktemp)"
RESPONSE_TMP="$(mktemp)"
trap 'rm -f "$IDENTITY_TMP" "$VERSION_TMP" "$RESPONSE_TMP"' EXIT

if [ "$NO_HOOKS" -eq 1 ]; then
  if [ "$THIS_CHECKOUT" -eq 1 ]; then
    python3 "$LIFECYCLE" identity "$TARGET" >"$IDENTITY_TMP"
  else
    python3 "$LIFECYCLE" identity --main "$TARGET" >"$IDENTITY_TMP"
  fi
  ROOT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["root"])' "$IDENTITY_TMP")"
  PROJECT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["project"])' "$IDENTITY_TMP")"
  "$BIN" --version >"$VERSION_TMP"
  python3 "$LIFECYCLE" version "$VERSION_TMP"
elif [ "$THIS_CHECKOUT" -eq 1 ]; then
  ROOT="$(git -C "$TARGET" rev-parse --show-toplevel 2>/dev/null || true)"
else
  ROOT="$(git -C "$TARGET" worktree list --porcelain 2>/dev/null |
    awk '/^worktree / { print substr($0, 10); exit }')"
fi
[ -n "$ROOT" ] || {
  printf 'not a Git repository: %s\n' "$TARGET" >&2
  exit 1
}

IGNORE="$ROOT/.cbmignore"

[ ! -L "$IGNORE" ] || {
  printf 'refusing symlink target: %s\n' "$IGNORE" >&2
  exit 1
}

BEGIN_IGNORE="# >>> cbm-onboard managed baseline — do not edit inside this block >>>"
END_IGNORE="# <<< cbm-onboard managed baseline <<<"
BEGIN_HOOK="# >>> cbm-onboard managed reindex >>>"
END_HOOK="# <<< cbm-onboard managed reindex <<<"
MANAGED_TMP="$(mktemp)"
OUTPUT_TMP="$(mktemp)"
HOOK_TMP="$(mktemp)"
trap 'rm -f "$IDENTITY_TMP" "$VERSION_TMP" "$RESPONSE_TMP" "$MANAGED_TMP" "$OUTPUT_TMP" "$HOOK_TMP"' EXIT

{
  printf '%s\n' "$BEGIN_IGNORE"
  printf '%s\n' \
    ".venv/" "venv/" "env/" "__pycache__/" "*.pyc" \
    ".pytest_cache/" ".mypy_cache/" ".ruff_cache/" ".tox/" \
    "node_modules/" "dist/" "build/" "*.egg-info/" \
    ".agentflow/" ".claude/worktrees/" ".codex/worktrees/" ".impeccable/" \
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

if [ "$NO_HOOKS" -eq 0 ]; then
COMMON_DIR="$(git -C "$ROOT" rev-parse --git-common-dir)"
case "$COMMON_DIR" in
  /*) : ;;
  *) COMMON_DIR="$ROOT/$COMMON_DIR" ;;
esac

# Honor an explicit core.hooksPath (e.g. a dotfiles-managed dispatcher):
# install alongside it rather than shadowing it under .git/hooks. Fall back
# to the repo-local, worktree-safe hooks dir when unset.
HOOKS_PATH="$(git -C "$ROOT" config --get core.hooksPath 2>/dev/null || true)"
if [ -n "$HOOKS_PATH" ]; then
  # git expands a leading tilde in a path-valued config; a global hooksPath is
  # commonly written that way, and joining it to the repo would create a literal
  # "~" directory inside the checkout.
  case "$HOOKS_PATH" in
    "~") HOOKS_PATH="$HOME" ;;
    "~/"*) HOOKS_PATH="$HOME/${HOOKS_PATH#\~/}" ;;
  esac
  case "$HOOKS_PATH" in
    /*) HOOKS_DIR="$HOOKS_PATH" ;;
    *) HOOKS_DIR="$ROOT/$HOOKS_PATH" ;;
  esac
else
  HOOKS_DIR="$COMMON_DIR/hooks"
fi

HOOK_SYMLINK_REFUSED=0
for HOOK_NAME in post-commit post-merge post-checkout; do
  HOOK="$HOOKS_DIR/$HOOK_NAME"
  HOOK_FILE="$HOOK"

  # A dotfiles-managed hooks dir is usually a farm of symlinks into the dotfiles
  # checkout. Edit the file the link resolves to: shadowing the link would be
  # clobbered by the next dotfiles run, and refusing leaves no hook at all.
  if [ -L "$HOOK" ]; then
    HOOK_FILE="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$HOOK")"
    if [ ! -f "$HOOK_FILE" ]; then
      printf 'refusing symlink without a regular-file target: %s\n' "$HOOK" >&2
      HOOK_SYMLINK_REFUSED=1
      continue
    fi
    printf 'following symlink %s to %s\n' "$HOOK" "$HOOK_FILE"
  fi

  : >"$HOOK_TMP"
  mkdir -p "$(dirname "$HOOK_FILE")"
  INSTALL_HOOK=1
  if [ -e "$HOOK_FILE" ]; then
    FIRST_LINE="$(sed -n '1p' "$HOOK_FILE")"
    if ! printf '%s\n' "$FIRST_LINE" |
      grep -Eq '^#!.*[/[:space:]](ba|da|k|z)?sh([[:space:]]|$)'; then
      printf 'SKIP hook installation: existing hook is not a shell script; left unchanged: %s\n' \
        "$HOOK_FILE" >&2
      INSTALL_HOOK=0
    fi
  else
    printf '%s\n' "#!/bin/sh" >"$HOOK_TMP"
  fi

  [ "$INSTALL_HOOK" -eq 1 ] || continue

  if [ -e "$HOOK_FILE" ]; then
    awk -v begin="$BEGIN_HOOK" -v end="$END_HOOK" '
      { lines[++n] = $0 }
      END {
        i = 1
        while (i <= n) {
          if (lines[i] ~ /^# codebase-memory-mcp: reindex on .* \(managed by cbm-onboard/) {
            i++
            if (i <= n && lines[i] ~ /^"[^"]*\/cbm-reindex\.sh"[ \t]*$/) i++
            continue
          }
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
    ' "$HOOK_FILE" >"$HOOK_TMP"
  fi
  {
    printf '\n%s\n' "$BEGIN_HOOK"
    if [ "$HOOK_NAME" = "post-checkout" ]; then
      printf '%s\n' '[ "$3" = "1" ] || exit 0'
    fi
    printf '"%s"\n' "$REINDEX"
    printf '%s\n' "$END_HOOK"
  } >>"$HOOK_TMP"
  cp "$HOOK_TMP" "$HOOK_FILE"
  chmod +x "$HOOK_FILE"
  printf '%s\n' "installed managed reindex command in $HOOK_FILE"
done

[ "$HOOK_SYMLINK_REFUSED" -eq 0 ] || exit 1
fi

if [ "${CBM_SKIP_INDEX:-0}" = "1" ]; then
  printf '%s\n' "skipped initial index (CBM_SKIP_INDEX=1): $ROOT"
elif [ "$NO_HOOKS" -eq 1 ]; then
  INDEX_EXIT=0
  "$BIN" cli --json index_repository --repo-path "$ROOT" --mode full --name "$PROJECT" \
    >"$RESPONSE_TMP" || INDEX_EXIT=$?
  python3 "$LIFECYCLE" response "$PROJECT" indexed false "$RESPONSE_TMP" || exit 1
  [ "$INDEX_EXIT" -eq 0 ] || {
    printf 'Codebase Memory index failed with exit %s\n' "$INDEX_EXIT" >&2
    exit 1
  }
  printf '%s\n' "indexed $ROOT as $PROJECT"
else
  PAYLOAD="$(python3 -c \
    'import json,sys; print(json.dumps({"repo_path": sys.argv[1], "mode": "full"}))' \
    "$ROOT")"
  "$BIN" cli index_repository "$PAYLOAD"
  printf '%s\n' "indexed $ROOT"
fi
