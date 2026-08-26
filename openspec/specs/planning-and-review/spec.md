# Planning and review routing

How ambiguous work becomes buildable, and how finished work gets reviewed.

## Behavior

* `/scope` is the triage front door for work that is not ready to build: it
  classifies the dominant uncertainty and routes to exactly one specialist
  skill, keeping a per-effort ledger under `docs/scope/` with decisions, open
  questions, and spawned tasks. Bounded work is admitted to build only with a
  risk contract copied into the authoritative artifact.
* `wayfinder` charts a large, foggy effort as a GitHub map issue with native
  child decision tickets, resolving one decision per session and filing
  build issues only when no open decision can invalidate them. Its map body,
  candidate-disposition protocol, and six persistent `wayfinder:*` labels are
  pinned by tests. (The pending epic-rework change supersedes this model.)
* `/review` is the review front door: it classifies the subject and routes to
  exactly one review skill — code review on two axes (repo standards, spec
  conformance), plan review as adversarial pre-build objection cycles capped
  at three panels, or a persona panel whose reviewer memory lives in a
  private data repo and never enters this one.
* `/orchestrate` flips a session into coordinator mode: the parent plans and
  reviews but delegates implementation to sub-agents routed by a benchmarked,
  provenance-stamped model routing table; stamped rows change only via a
  benchmark replay. Literal invocation requests the work order or task prompt
  plus only the repository code and documentation needed for every mandatory
  dispatch, including nested review and nested Orchestrate work. A Codex UI
  parent admits OpenAI Codex; a Claude Code parent admits OpenAI Codex or
  Anthropic Claude under existing routing. Credentials, secrets, patient data,
  `.env`, and real database contents are excluded.
* Automatic activation outside an invoked Ticket or Orchestrate parent asks once
  before its first external dispatch with the same payload, destination or
  destination matrix, and exclusions. Adapter escalation rationales repeat those
  terms so a guardian can match intent, but assistant-authored rationale does not
  create authorization.

## Invariants

* Planning artifacts record decisions once, in one home: resolutions in their
  ticket, lasting rulings as ADRs in `docs/adr/`, work orders on the tracker.
* Review verdicts are grounded in files read or commands run, never in the
  plan's own claims about the system.
* The worker-egress declaration changes neither pack-owned adapter isolation nor
  platform approval policy and does not claim to filter prompt bytes.

## Dependents

The ticket workflow's triage verb calls into `/scope`; persona review's
containment rule binds every calling skill's committed artifacts.
