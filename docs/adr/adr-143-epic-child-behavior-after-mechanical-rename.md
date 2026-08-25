# ADR 143 — Epic-child behavior after the mechanical rename

## Context

ADR 51 records the legacy `wayfinder` taxonomy and its mechanical path move. The
epic proposal evolved that driver into `epic`, while deliberately keeping the move
separate from the lifecycle behavior that its child tickets need.

## Decision

`epic` is the evolved driver. Shared epic-child behavior follows the mechanical path
move in separate children, so the rename and lifecycle contract remain independently
reviewable. This record amends ADR 51 without renaming or rewriting that legacy
record.

## Consequences

Epic-child triage, execution, follow-up handling, and close-out use the evolved
driver's settled lifecycle contract. This ADR does not amend the parent epic's
close-out or baseline decisions.
