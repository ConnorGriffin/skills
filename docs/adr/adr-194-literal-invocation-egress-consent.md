# ADR 194 — Literal workflow invocation carries bounded worker-egress consent

Status: accepted (2026-08-26)

## Context

ADR 149 requires every model dispatch defined by this pack to use the pack-owned
CLI adapters. That boundary preserves a fixed checkout and sandbox, explicit model
and effort, resumable identity, scoped recovery, and measurable usage. Issue #146
separately established that invoking a mandatory-review workflow authorizes the
required sub-agent dispatch.

A model dispatch also sends task and repository context to a new model invocation.
Generic delegation authority does not identify that payload or destination, so an
approval guardian can correctly fail closed even though the workflow itself
requires a reviewer. A Codex UI parent admits only OpenAI Codex workers; a Claude
Code parent may admit OpenAI Codex or Anthropic Claude workers under existing
routing.

## Decision

Literal user invocation of `/ticket triage`, `/ticket start`, `/ticket revise`, or
`/orchestrate` requests the bounded repository egress those workflows require:
the task prompt or work order plus only the repository code and documentation needed
for the delegated task, sent to an isolated worker on the service admitted for the
parent: OpenAI's Codex model service for a Codex UI parent, or OpenAI's Codex model
service or Anthropic's Claude model service for a Claude Code parent as selected by
existing routing.
Credentials, secrets, patient data, `.env`, and real database contents are excluded.

That invocation covers every mandatory worker dispatch the selected workflow
routes, including nested review and nested Orchestrate work. Automatic activation
outside an invoked parent workflow does not acquire the consent; it asks once
before the first external dispatch, naming the same payload, applicable
destination or destination matrix, and exclusions. `/ticket finalize` grants no
worker-egress consent. This is an intent-level workflow contract: it adds no
command parser, provenance artifact, approval state machine, or byte filter.
Each skill's OpenAI manifest default prompt states the same bounded request so a
UI-assisted invocation places it directly in trusted user text.

The skills remain model-invoked. Making them user-invoked-only would remove real
composition paths: `epic` reaches `ticket`, and chunked ticket execution reaches
`orchestrate`.

Generic delegation authority and egress consent remain separate contracts. The
former permits the required worker to exist; the latter permits the bounded bytes
to be sent to the named destination. Each adapter-specific approval rationale
repeats the egress contract in its escalation justification but does not claim that
assistant-authored rationale creates user authorization. These are guardian-facing
instruction contracts, not byte-level prompt filters or changes to platform approval
policy.

## Consequences

* A literal workflow command can carry complete consent without a second prose
  round-trip.
* UI-assisted invocation presents the same request in its default user prompt.
* Mandatory nested routing does not trigger redundant consent prompts, while
  automatic activation outside an invoked workflow still asks once.
* Pack-owned worker isolation and recovery remain unchanged.
* A future approval-policy change may still require one explicit prompt; the skill
  reports the stop and never works around the guardian.
