# Design

## ADR 212 — Truthful verification reporting is a prose contract

The worker-facing rule lives immediately before the existing coordinator
verification obligation. It distinguishes the named full command from supplemental
checks, hooks, bypasses, and incomplete runs without changing routing, adapters,
lifecycle scripts, or coordinator escalation behavior.

The assurance boundary is intentional: a whitespace-normalized prose pin guards the
load-bearing partial-is-not-full sentence. No parser, evidence protocol, provenance
record, or runtime enforcement is added.
