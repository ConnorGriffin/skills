# Design

## ADR 258 — Generate identical grant blocks and check contextual clauses

**Context.** The worker-egress consent grant has thirteen live occurrences. Three
review-dispatch blocks are byte-identical. The other ten occurrences deliberately
differ: frontmatter descriptions are byte-capped, invocation bodies explain the
parent-specific destination matrix, OpenAI prompts narrow the destination, and
adapter references name their selected provider. Generating every occurrence from
one template would either erase those distinctions or introduce a templating
interface as complicated as the prose it replaces. Checking everything would
leave the three identical blocks hand-synchronized.

**Decision.** Use a hybrid mechanism. A canonical six-line block generates only
the three byte-identical review-dispatch spans. A per-surface registry checks the
ten contextual occurrences for their payload, safe-fixture qualifier, exclusions,
and applicable destinations. The same check enforces the 1,024 UTF-8-byte cap on
both SKILL.md frontmatter descriptions.

The authority is repository-level and test/CI-time only. Individually installed
skills cannot depend on a file outside their own directory, so every published
surface keeps complete prose. The sync/check script is maintenance tooling, not
runtime consent enforcement.

**Consequences.** A wording change starts in one canonical source. Identical
dispatch blocks are regenerated, while deliberate contextual copies fail with a
surface-and-clause message until updated. Safe-fixture widening, exclusion loss,
unsynced generation, and description overflow are all red tests. The current
grant bytes and meaning remain unchanged.
