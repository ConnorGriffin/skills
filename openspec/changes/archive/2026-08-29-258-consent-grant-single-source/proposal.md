# Single-source the worker-egress consent grant

## Why

The worker-egress consent grant is repeated across thirteen live Ticket and
Orchestrate surfaces. Three copies are byte-identical, while the remaining ten
are deliberately wrapped, trimmed, or scoped for their own context. Tests pin
the wording after the fact, but a wording change still requires hand-editing all
copies and rebuilding the same inventory in assertions.

## What changes

- Store the canonical six-line dispatch block and the required clauses for every
  other occurrence in one repository-level source.
- Provide a stdlib-only `sync`/`check` script. `sync` owns only the three
  byte-identical dispatch blocks; `check` verifies those blocks, all other clause
  surfaces, and both SKILL.md frontmatter byte caps.
- Drive the contract through the script's public interface, including isolated
  regressions for every safe-fixture qualifier and for canonical-source drift.

Published skill copies remain self-contained prose. The grant's wording,
meaning, destinations, and exclusions do not change.
