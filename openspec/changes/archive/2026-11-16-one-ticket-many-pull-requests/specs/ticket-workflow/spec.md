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
pull-request-sized pieces on the ticket and lock one piece at a time, each lock
bounded by its own expected diff. Triage MUST record which slicing traits fired.
Triage MUST NOT ask whether to split the ticket and MUST file child issues only when
the operator asks. Finalize MUST leave the ticket open while a checklist piece
remains.

#### Scenario: Two slicing traits fire

- **WHEN** grounding finds two or more slicing traits, or a projected peak past the
  session band
- **THEN** triage posts a pieces checklist on the ticket, locks the first piece, and
  files no child issues

#### Scenario: A piece merges with pieces remaining

- **WHEN** finalize runs on a merged piece and the checklist has an open box
- **THEN** it ticks the merged piece, leaves the ticket open, and names the next
  piece, and the next triage locks that piece without asking
