# ADR 97 — Compatible engines precede hardening adapters

Date: 2026-08-22
Status: accepted
Issue: https://github.com/ConnorGriffin/skills/issues/97

## Context

The giant Harmonic platform brief is superseded. It attempted to settle a
hardening platform before the repository had evidence that the engines,
tool-runtime boundary, or cross-language contract were compatible. Map 85
still requires an evidence-first pilot with two real Harmonic adapters and a
later five-ticket dogfood experiment, while preserving the committed workflow
until its introducing pull request merges.

## Decision

First run a bounded compatibility spike against real Harmonic Python and
JavaScript changes. The spike preserves each third party's native reports and
must explicitly prove or reject a supported CI-only tool runtime while the
Python 3.9 application floor stays fixed. Only after that evidence exists will
we specify independent thin adapters that map `pass`, `fail`, `error`, or
`not-applicable`.

Only after two adapters run may Skills #89 decide whether a shared seam
survives the deletion test. Custom worktrees, elaborate schemas, registries,
applicability engines, fixture generators, process orchestration, and reusable
CRAP tooling are deferred until observed failures or a separate product
decision justify them.

The existing `/ticket` workflow remains authoritative. Its QA and public-
interface testing, bounded review, survivor, worktree isolation, locked
handoffs, human merge authority, and five-ticket dogfood decisions remain in
force; the dogfood decision uses combined evidence, including human-requested
corrections and post-merge defects, rather than token or review-round counts
alone.

## Consequences

- Compatibility evidence becomes the gate for adapter shape and runtime
  support; the Python application floor is not raised to make the tool pass.
- Native reports remain available for diagnosis while the thin adapters expose
  only the four pilot outcomes.
- The shared seam remains a hypothesis until two real adapters have run, and
  the deletion test can reject it without first paying for a platform.
- Deferred machinery is not part of this recovery boundary. It can be proposed
  later when a failure or an independent product decision supplies evidence.
