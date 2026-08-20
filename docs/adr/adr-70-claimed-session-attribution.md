# ADR 70 — Ticket telemetry records attribution instead of inferring it

Date: 2026-08-20
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/70

## Context

The ticket telemetry answers one question: which sessions worked this ticket, and
what did they peak at. The peak feeds the slicing rubric, which decides whether
future work runs as one order or several.

It answered the first half by searching every local transcript for the ticket's
id in operator prose. That is inference, and it failed in both directions within
a single day of use:

- Ticket 62 recorded a peak of 296,596 tokens from a session dated sixteen days
  before the ticket existed. A bare substring test matched a benchmark
  percentage, a hex task id, a commit sha, a line range, and another
  repository's pull request number.
- Tightening the match to a delimited reference ([#64]) fixed those, and then
  ticket 64 recorded `no-data` while ticket 68 recorded a peak of 36,470 from an
  unrelated session in another directory. The sessions that did the work were
  invisible, because an agent had filed both tickets and the operator never
  typed either id.
- `--project` was a substring filter, so a worktree directory whose name
  contained the repository's name counted as the repository.

Each fix refined the guess. None of them could stop being a guess, because the
prose a session contains is not evidence of what that session worked on.

## Decision

The verbs record their own attribution. `ticket.py claim <ticket-id>` writes one
line naming the session, its agent, and its working directory; every verb claims
its session as an early step. `scan` and `record` read those claims and resolve
each session's transcript by exact id.

The matching machinery is deleted rather than kept as a fallback: the reference
regex, the operator-typed text extractor, the substring prefilter, and the old
`scan`/`record --project` filter. Claim's `--project` metadata remains: it records
the actual working directory of the claimed session, including a dispatched
worker's chunk worktree. A fallback would reintroduce the failure mode on exactly
the tickets where claims are absent, and silently, which is how the first bad
record was written.

A session id comes from the agent's own environment (`CLAUDE_CODE_SESSION_ID`,
`CODEX_SESSION_ID`) or from `--session` with `--agent`, so a coordinator can
claim on behalf of a dispatched worker. Two visible ids are a refusal rather
than a preference order: a worker launched from another agent's session
inherits that session's variable, and choosing between them would record the
coordinator's transcript against the worker's ticket. Which agent wrote a session is part of
the claim because it decides both where the transcript lives and how context is
counted: a Claude transcript sums three usage fields per turn, while a Codex
rollout reports one input total that already contains its cached part.

## Consequences

- A ticket worked before this landed has no claims and reports `no-data`.
  Existing telemetry records and the rubric's anchor rows stay as they are; the
  numbers already taken do not become recoverable.
- A claim whose transcript has been deleted is reported under `unreadable`
  rather than counted as a session that cost nothing.
- Claiming is not a gate. A verb whose claim fails says so in one line and
  continues, because a measurement must never block the work it measures.
- The telemetry can now undercount only by a verb failing to claim, which is a
  visible absence, rather than by matching the wrong session, which was not.
