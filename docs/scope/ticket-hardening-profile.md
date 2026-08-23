# Scope: /ticket hardening profile (issue 103)

Opt-in `/ticket` profile that replaces agent review rounds with a deterministic
hardening command plus a human QA script.

## Decisions

_(appended as each settles)_

## Open questions

- Q1 sequencing against `/clean` (issue 102)
- Q2 profile selection mechanism
- Q3 target repo with no `Harden:` declaration
- Q4 stop condition for the hardening loop
- Q5 QA script: every order or profile-only
- Q6 disposition of open siblings 89, 92, 94, 95

## Grounding (verified this session)

- No profile mechanism exists in `skills/drivers/ticket/` today; `Review depth:`
  and `Surface lifecycle:` are the only per-order switches.
- `/clean` does not exist in the pack; issue 102 is open and unbuilt.
- This repo declares no `Harden:` line; it is a markdown pack with a Python
  validator and unittest suite.
- `profile:` and `ui-surfaces:` in `AGENTS.md` are declared but consumed by no
  code in this repo, so a repo-facts declaration line has precedent.
- ADR 97 keeps the current `/ticket` workflow authoritative and defers adapters
  until a compatibility spike; issue 103 stays inside that boundary by using a
  raw command line instead of adapters.
- Issues 87, 88, 91, 93, 96 are already closed; 89, 92, 94, 95 are open and
  overlap issue 103's substance.

## Spawned tasks

_(none yet)_
