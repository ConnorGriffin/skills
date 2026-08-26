# Reviewer-egress consent from literal workflow invocation

## Why

`ticket` and `orchestrate` deliberately dispatch through pack-owned CLI workers,
but their invocation contracts name delegation without naming the repository
payload or the OpenAI Codex destination. A Codex approval guardian can therefore
treat the launch as unauthorized sensitive egress even after the user deliberately
invoked the workflow.

## What changes

* Literal user invocation of `/ticket triage`, `/ticket start`, `/ticket revise`,
  or `/orchestrate` becomes an explicit request to send the bounded task prompt
  and necessary repository code/documentation to an isolated worker on OpenAI's
  Codex model service.
* Automatic or nested skill activation does not acquire that consent. It must
  inherit an equally explicit contract from the literal parent workflow or ask
  once before the first external dispatch.
* Each skill's OpenAI manifest default prompt carries the same bounded request so
  UI-assisted invocation places the payload and destination in trusted user text.
* The Codex-parent dispatch reference repeats the payload and destination in its
  escalation rationale so the guardian can match the planned action to the
  invocation contract.
* The pack-owned worker adapters, model routing, sandboxing, lifecycle recovery,
  and usage measurement remain unchanged.

## Risk contract

* **Must prevent:** silent repository egress from automatic routing; transmission
  of credentials, secrets, patient data, `.env`, or real database contents;
  weakening the worker sandbox or replacing the pack adapter.
* **Must recover:** none. A denied guardian check stops before egress and can be
  retried only after exact user consent.
* **Accepted failure:** a guardian whose policy or transcript shape changes may
  still request one explicit confirmation; the workflow stops clearly instead of
  bypassing or repeatedly rephrasing the request.
* **Unsupported:** treating loose natural-language activation, nested skill
  activation without a parent consent contract, or `/ticket finalize` as consent
  for model dispatch.
* **Evidence owed:** contract tests prove the literal invocation surface and OpenAI
  default prompt name the payload and destination, automatic/nested activation
  retains a consent gate, the dispatch rationale repeats the same terms, and
  existing adapter/lifecycle tests remain green.

Why: approval semantics govern private repository egress and must fail closed
without breaking the isolation guarantees that motivated pack-owned dispatch.
Disposition: inline in issue #194 and ADR 194.
