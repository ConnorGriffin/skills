# Retire the agentflow premise

## Why

The former agentflow consumer no longer exists, leaving its evidence and pinning
contracts write-only.

## What changes

Remove that premise and its evidence-v2 enforcement while retaining actual pack
integrity checks and immutable published release tags.

## Risk contract

The validator, tests, DCO, syntax checks, fresh-install smoke test, and
AGENTS.md/CLAUDE.md identity remain required. Historical records remain unchanged.
