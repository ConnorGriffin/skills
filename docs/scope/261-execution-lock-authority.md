# Scope ledger — 261 execution-lock authority

Turn the #261 spike findings (thin execution lock pinned to a durable change
source) into a locked build work order on #261.

## Decisions

- Route: interview mode; the spike findings are the written plan, and its nine
  attended decisions are the open frontier. inline
- The work order lands on #261 itself (user asked to turn this issue into the
  workable ticket). inline

## Decisions (round 1, settled 2026-08-30)

- Identifier syntax: plain positional task/requirement numbers, valid within the
  pinned commit; no inline ID markers or hashes (operator: single-operator flow,
  nobody reorders under a lock; the pin freezes the bytes). inline
- Checked `tasks.md` item = implemented and verified, checked by the executor.
  inline
- Ordinary tickets own their whole change; only epic children select subsets of
  a shared parent change. inline
- Every source amendment requires a newer lock pinning the new commit, including
  during revise. inline
- Pinned commits stay reachable forever via merged history; no expiry handling.
  inline
- Investigations get an explicit read-only lock only when they dispatch a
  bounded worker; otherwise issue + findings suffice. inline
- Strict OpenSpec validation at triage and at start. inline
- Legacy `WORK ORDER` comments never sunset; the legacy locator stays, and any
  supersession uses the new lock protocol. inline
- Expected-diff allowlist stays explicit in the lock, never derived. inline

Defaults Q3–Q9 adopted from the spike findings' recommendations without
individual interrogation (operator pushback: obvious defaults); overrulable at
draft review.

### Risk contract

- **Must prevent:** silent execution of an unauthorized or amended source
  (wrong commit, archived change, expanded scope); secret exposure; silent
  incorrect success.
- **Must recover:** nothing automatic — validation failures stop cleanly.
- **Accepted failure:** a stale or invalid pin refuses execution with a clear
  message and routes to attended re-triage.
- **Unsupported:** retrofitting pins into already-posted legacy orders;
  multi-operator concurrent edits to one active change.
- **Evidence owed:** lock recognition/parsing, fail-closed validation matrix
  (missing/stale/amended/archived/invalid source), legacy-order path, chunk
  sub-lock standalone sufficiency — via the existing test suites.

Why: single-operator workflow tooling; the harm ceiling is executing the wrong
plan, which validation must catch. Disposition: inline (copied into the work
order).

## Spawned tasks

(none yet)
