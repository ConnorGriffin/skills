# Effort enums

Each adapter validates its own set. They are not the same set.

## claude

```
$ claude --help | grep -A1 -- "--effort"
  --effort <level>                      Effort level for the current session
                                        (low, medium, high, xhigh, max)
```

## codex (live API probe, 2026-08-27)

The codex CLI does NOT validate this value locally — a bogus value starts the
session and fails at the API:

```
$ printf hi | codex exec -m gpt-5.6-luna -c model_reasoning_effort=bogus --sandbox read-only --skip-git-repo-check
reasoning effort: bogus
ERROR: { ... }   # accepted locally, rejected by the API
```

The live Codex 5.6 probe exercised `codex-worker.py start --model
gpt-5.6-luna --sandbox read-only --effort <E>`:

| Effort | Result |
| --- | --- |
| `none` | The adapter previously rejected it locally. The API accepts it. |
| `max` | The adapter previously rejected it locally. The API accepts it. |
| `minimal` | The adapter accepted it, then the API rejected it with HTTP 400. |
| `low` | Works. |
| `xhigh` | Works. |

The model returned: `Unsupported value: 'minimal' ... Supported values are:
'none', 'low', 'medium', 'high', 'xhigh', and 'max'.`

The adapter enum is therefore `none|low|medium|high|xhigh|max`. This is the
adapter's local guard; the Codex CLI itself still sends arbitrary values to the
API.

### Superseded record (2026-08-24)

The earlier configuration-reference record stated
`minimal|low|medium|high|xhigh`. It is retained as the historical source of the
old adapter guard, but is superseded by the 2026-08-27 live API probe above.
