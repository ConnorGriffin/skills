# Tasks

- [ ] Expand exact-id Codex rollout discovery across the active and archived
      roots without collapsing distinct resumed rollouts.
- [ ] Add public-command tests for active-only, archived-only,
      active-plus-archived, and genuinely missing rollout discovery through
      `scan` and `record`, including the 228,055-token flat-order verdict
      reproduced in `docs/scope/290-generated-facts.md`.
- [ ] Preserve claim attribution, Claude discovery, rollout parsing, verdict
      thresholds, and existing missing-rollout behavior.
- [ ] Run `openspec validate 290-measure-archived-codex-rollouts --strict` and
      the full repository verification command from `AGENTS.md`.
