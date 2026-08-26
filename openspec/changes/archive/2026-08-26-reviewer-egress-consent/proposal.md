# Reviewer-egress consent from literal workflow invocation

## Why

`ticket` and `orchestrate` deliberately dispatch through pack-owned CLI workers,
but their invocation contracts name delegation without naming the repository
payload or the admitted external destination. An approval guardian can therefore
treat the launch as unauthorized sensitive egress even after the user deliberately
invoked the workflow.

## What changes

* Literal user invocation of `/ticket triage`, `/ticket start`, `/ticket revise`,
  or `/orchestrate` becomes an explicit request to send the bounded task prompt
  and necessary repository code/documentation to an isolated worker on OpenAI
  Codex for a Codex UI parent, or OpenAI Codex or Anthropic Claude for a Claude
  Code parent as selected by existing routing.
* That invocation covers mandatory nested review and Orchestrate dispatches.
  Automatic activation outside an invoked parent workflow asks once before its
  first external dispatch; no parser or approval state machine is added.
* Each skill's OpenAI manifest default prompt carries the same bounded request so
  UI-assisted invocation places the payload and destination in trusted user text.
* Each adapter dispatch reference repeats its applicable payload, destination,
  exclusions, and invoked-workflow coverage so a guardian can match the planned
  action to the invocation contract.
* The pack-owned worker adapters, model routing, sandboxing, lifecycle recovery,
  and usage measurement remain unchanged.

## Risk contract

* **Must prevent at the instruction-contract layer:** extending consent beyond an
  invoked Ticket or Orchestrate workflow; authorizing credentials, secrets,
  patient data, `.env`, or real database contents; weakening the worker sandbox
  or replacing the pack adapter. This change does not inspect or filter prompt
  bytes.
* **Must recover:** none. Automatic activation outside an invoked parent asks once
  with the same material terms. A denial stops before egress.
* **Accepted failure:** a guardian whose policy or transcript shape changes may
  still request one explicit confirmation; the workflow stops clearly instead of
  bypassing or repeatedly rephrasing the request.
* **Unsupported:** treating automatic activation outside an invoked parent or
  `/ticket finalize` as consent for model dispatch.
* **Evidence owed:** static contract tests prove the invocation surfaces name the
  payload, destination matrix, exclusions, and mandatory nested-dispatch coverage;
  the applicable default prompt and dispatch rationale repeat those terms; existing
  adapter/lifecycle tests remain green. They do not claim to prove guardian
  behavior or byte filtering.

Why: approval semantics govern private repository egress and must fail closed
without breaking the isolation guarantees that motivated pack-owned dispatch.
Disposition: inline in issue #194 and ADR 194.
