# ADR 107 — Ticket telemetry keys claims and records by repository, not just ticket id

Date: 2026-08-23
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/107

## Context

ADR 70 made `claim` record its own attribution instead of inferring it, so
`scan` and `record` measure exactly the sessions that claimed a ticket rather
than guessing from transcript prose. That fixed *which sessions* count. It did
not fix *which ticket*: `read_claims` filters only on `ticket_id`, and two
repositories that both happen to number an issue, say, 42 write claims that
`scan` cannot tell apart. A claim made against `ConnorGriffin/skills#42`
would be folded into the peak reported for a different repository's ticket
42, understating one and overstating the other, and neither number would be
visibly wrong — the ticket id alone gave no reason to suspect it.

`claim` already resolves a real, checkout-derived value before this change:
`arguments.project or str(Path.cwd())` is always a filesystem path — either
the claiming process's own working directory, or a coordinator-supplied
`--project <chunk-worktree>` naming a dispatched worker's real checkout
(`skills/drivers/ticket/references/coordinator-mode.md` requires exactly
this). It was never a hand-typed label. What was missing was turning that
path into a stable repository identity two different checkouts of the same
repository — the control checkout and a ticket worktree, say — would both
resolve to.

## Decision

`ticket.py` gains `resolve_repo(path) -> Optional[str]`, tried in order and
never raising:

1. `git -C <path> remote get-url origin`, normalized so an ssh remote
   (`git@host:owner/repo.git`) and an https remote
   (`https://host/owner/repo.git`) for the same repository collide to one
   string (`host/owner/repo`).
2. On failure (no origin remote, or `path` is not a checkout at all),
   `git -C <path> rev-parse --show-toplevel`, returned as-is.
3. On failure of both, `None`.

`command_claim` calls this on the same `project` value it already computes
and stores the result as a new `repo` field on the claim, alongside the
existing `project` field. No new `--repo` flag: repository identity is
always derived from a checkout path already in play, never typed.

`scan(ticket_id, projects_dir, current_repo)` takes the current repository as
a third argument (`command_scan` and `command_record` compute it once, from
`Path.cwd()` — no new CLI flag, since both already run from inside the
ticket's own worktree) and partitions every claim `read_claims` returns into
three groups: claims whose `repo` matches `current_repo` (these alone feed
`session_count`, `claim_count`, `peak_context`, `subagent_peak`, and
`sessions`, exactly as before); claims whose `repo` is set but differs
(counted only, in `excluded_claims`); and claims whose `repo` is missing or
`null` (named by session id in `unattributable`). `scan`'s result also
reports `repo: current_repo`, so a reader can see which repository was
measured. `command_record` persists all three new fields into
`telemetry.jsonl`.

A claim with no resolvable repository — written before this field existed,
or one where resolution itself failed — is reported as unattributable, never
counted into either repository's measurement. This mirrors ADR 70's decision
for an unreadable transcript: a measurement that cannot attribute itself is a
visible gap, not a silent zero and not a silent inclusion.
`verdict()`'s `no-data` reason now distinguishes the two shapes of nothing:
"no session claimed this ticket" (nothing at all) from "this ticket had
claims, but none of them from this repository" (something claimed it, just
not the repository asking).

## Consequences

- Two repositories sharing a ticket id now measure independently: each
  repository's own `scan` reports only its own sessions, and sees the other
  repository's claim named in `excluded_claims` rather than folded in.
- A claim written before this change has no `repo` field. It reports under
  `unattributable` rather than being silently absorbed into whichever
  repository happens to scan it next, or silently zeroing out a ticket's
  measurement.
- A checkout that loses its origin remote between claiming and scanning
  resolves to a different identity (its toplevel path) than before — silently,
  from telemetry's point of view, the same way a moved or renamed remote
  already made ADR 70's session ids brittle to environment drift.
- Two checkouts of the same repository that both lack an origin remote
  resolve to two different toplevel-based identities and are never treated as
  the same repository. This is a known gap, not a case this change closes:
  the origin remote is the only signal strong enough to collide two distinct
  filesystem paths into one identity.
- `references/slicing.md`'s existing anchor rows, which already collide
  across repositories by ticket id, are unchanged by this ticket; disambiguating
  them is out of scope here and remains the operator's call in an ordinary
  pull request.
