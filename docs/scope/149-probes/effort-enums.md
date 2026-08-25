# Effort enums, captured 2026-08-24

Each adapter validates its own set. They are not the same set.

## claude

```
$ claude --help | grep -A1 -- "--effort"
  --effort <level>                      Effort level for the current session
                                        (low, medium, high, xhigh, max)
```

## codex

The codex CLI does NOT validate this value locally — a bogus value starts the
session and fails at the API:

```
$ printf hi | codex exec -m gpt-5.6-luna -c model_reasoning_effort=bogus --sandbox read-only --skip-git-repo-check
reasoning effort: bogus
ERROR: { ... }   # accepted locally, rejected by the API
```

Authoritative set, from the Codex configuration reference
(https://learn.chatgpt.com/docs/config-file/config-reference):

> model_reasoning_effort: "minimal | low | medium | high | xhigh" (Responses API only;
> "xhigh is model-dependent")
