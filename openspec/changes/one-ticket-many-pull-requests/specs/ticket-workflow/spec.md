## REMOVED Requirements

### Requirement: Oversized work becomes tracked child issues

**Reason**: Splitting into child issues by pull-request or repo count was rejected by
the operator every time it was offered.

**Migration**: Use "Multi-pull-request work stays on one ticket". Tickets already
tracking child issues finish on that path.

## ADDED Requirements

### Requirement: Multi-pull-request work stays on one ticket

Triage MUST keep work that spans repos, needs several pull requests, follows a UI
lock, or will not fit one session on its ticket. It MUST post a checklist of
pull-request-sized pieces on the ticket and lock a work order for every piece in
the same pass, each bounded by its own expected diff and naming what it waits on.
Triage MAY defer only a piece whose outcome waits on a spike piece. Triage MUST record which slicing traits fired.
Triage MUST NOT ask whether to split the ticket and MUST file child issues only when
the operator asks. Finalize MUST leave the ticket open while a checklist piece
remains.

#### Scenario: Two slicing traits fire

- **WHEN** grounding finds two or more slicing traits, or a projected peak past the
  session band
- **THEN** triage posts a pieces checklist on the ticket, locks an order for every
  piece after one approval, and files no child issues

#### Scenario: A piece waits on unmerged work

- **WHEN** start runs and the first unchecked piece's order waits on a piece or ticket
  that has not merged
- **THEN** start refuses and names what it waits on, and the order stays valid

#### Scenario: A piece merges with pieces remaining

- **WHEN** finalize runs on a merged piece and the checklist has an open box
- **THEN** it ticks the merged piece, leaves the ticket open, and names the next
  piece, and reports start as the next step
