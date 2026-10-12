# workflow-continuation Specification

## Purpose

Keep an authorized workflow moving through answered decisions and completed
helpers, present decisions in a host-compatible form, reuse admitted decisions
without redundant approval, and preserve ticket ownership when UI work nests
inside a ticket.

## Requirements

### Requirement: Parent continuation

An answered decision or completed helper MUST resume the next authorized caller step; an actual unanswered decision, denial, failed admission, missing required evidence, or explicit handoff MUST stop only the dependent work.

#### Scenario: A helper returns before triage has posted its lock

- **WHEN** a nested helper result is complete and another authorized triage step remains
- **THEN** the caller performs that step rather than ending on acknowledgment

### Requirement: Host-compatible decisions

Interview presentation MUST preserve the locked form where permitted and MUST obey higher-priority host restrictions elsewhere. A fallback MUST expose substantive considered alternatives and their costs, retain stable identifiers, accept free-form rejection or delegation, and wait for required answers.

#### Scenario: A host forbids textual multiple-choice questions

- **WHEN** the operator needs to decide between materially different implementations under that restriction
- **THEN** the agent gives an allowed explanatory comparison and concise question without hiding alternatives or assuming agreement

### Requirement: Inherited decisions and bounded evidence

Helpers MUST consume admitted decisions covering the same scope without redundant approval, retain genuine new decisions, and verify supported behavior proportionately without substituting static prose checks for behavioral evidence.

#### Scenario: TDD receives settled behavior and interface decisions

- **WHEN** the admitted lock covers its proposed interface and test behavior
- **THEN** TDD proceeds while a materially new decision still returns to the operator

### Requirement: UI preparation and ownership

Ticket triage MAY prepare first-revision behavior evidence only after safe-start and manufactured data are verified; the required ledger and replay MUST be frozen before lock admission. Nested UI work MUST retain the admitted checkout/base and existing sanction requirements.

#### Scenario: A shipped surface has no frozen ledger

- **WHEN** safe-start and manufactured data are verified in the ticket checkout
- **THEN** triage prepares and freezes evidence before source admission without starting implementation or replacing the inherited base
