# ADR 195 — Retire the agentflow premise

Status: accepted (2026-08-26)

## Context

agentflow no longer consumes this pack. The pack is installed by the standard
`skills` CLI and read directly by interactive Claude Code and Codex sessions.
Its content-hash consumer claim, evidence-v2 emission contract, and byte-exact
prose-pin regime therefore enforced write-only ceremony rather than live use.

## Decision

Remove the consumer claim, evidence-v2 documents and validator checks, evidence
instructions, and test constants copied from skill prose. Preserve behavioral
predicates for load-bearing cross-skill rules. Preserve equality checks only when
they compare two live copies of one required contract.

Published release tags remain immutable history: installers may pin any published
ref. This is independent of any former daemon. Future per-repository reviewer
memory, if needed, owns its own reader and contract in #197.

## Consequences

The structural validator, unit suite, syntax checks, DCO gate, and fresh
skills-CLI install smoke test remain the pack's enforcement. Future edits have no
evidence envelope to maintain unless a live consumer introduces one.
