# Keep authorized workflows moving

## Why

Issue #293 reports that a decision acknowledgment or completed helper can end an agent turn before the caller finishes its authorized workflow. A supplied screenshot shows reviewed scope reported as a stopping point before ticket triage produced its work order. A disposable Git probe also reproduces loss of pre-existing edits in the current clean rollback instructions. These are separate observed failures; the audit does not establish one model-level cause.

## What Changes

- Clarify continuation, inherited authorization, and helper return in existing prose authorities and consumers.
- Preserve useful alternatives in host-compatible interviews; admit explicitly selected Astra executors separately from reviewer rankings.
- Give first-revision UI behavior evidence a permitted producer in triage and preserve inherited ticket checkout ownership.
- Correct bounded stale instructions and CBM failure diagnostics; disposition all audit findings without absorbing separate worker infrastructure or private-machine work.

## Capabilities

### New Capabilities

- `workflow-continuation`: composed helper return, truthful failure reporting, host-compatible decisions, and ticket/UI admission.

### Modified Capabilities

None. Existing baseline requirements remain in force; the new capability specifies their composition.

## Impact

One ticket, one implementation PR, two serial chunks. The closed source inventory is in `inventory.md`. This is primarily a prose correction. The only planned production executable edit is actionable stderr from the existing CBM lifecycle helper while preserving its stdout and exit-code contract. No new dependencies, policy framework, benchmark campaign, global configuration, bundled-cache edits, or live application implementation.
