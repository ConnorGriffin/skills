# Generated facts — ticket 290

## A. Current Codex rollout root

Command:

```text
rg -n "CODEX_SESSIONS_DIR|return sorted\(CODEX_SESSIONS_DIR" skills/drivers/ticket/scripts/ticket.py
```

Output:

```text
38:CODEX_SESSIONS_DIR = Path(
244:        return sorted(CODEX_SESSIONS_DIR.glob(f"**/rollout-*-{session_id}.jsonl"))
```

## B. Archived discovery and threshold behavior

Command:

```text
/opt/homebrew/bin/python3.14 docs/scope/290-probes/reproduce.py
```

Output:

```json
{
  "archived_only": {
    "session_count": 0,
    "unreadable": [
      "codex-archived-290"
    ]
  },
  "active_threshold": {
    "peak_context": 228055,
    "verdict": "under-sliced",
    "reason": "flat order execution peaked at 228,055 tokens, past the 180,000 degradation band"
  }
}
```

## C. Redacted real archive inventory

Command:

```text
/opt/homebrew/bin/python3.14 docs/scope/290-probes/inspect-real-archive.py
```

Output:

```json
{
  "root": "archived_sessions",
  "filename_shape": "rollout-<timestamp>-<session-id>.jsonl",
  "matching_rollout_exists": true
}
```

## D. Host interpreter versions

Command:

```text
python3 --version
```

Output:

```text
Python 3.9.6
```

Command:

```text
/opt/homebrew/bin/python3.14 --version
```

Output:

```text
Python 3.14.7
```
