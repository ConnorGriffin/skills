# Scope ledger — 195 retire the agentflow premise

## Decisions

- Classification: `code` — lands as one PR on `codex/195-retire-agentflow-premise`. Why: repo facts, spec, validator, and tests all change together. inline
- Grounding verified live (2026-08-26): AGENTS.md/CLAUDE.md byte-identical premise at lines 3-5 and 37-39; validate.py:51-56 hardcodes `ConnorGriffin/agentflow` provenance; 32 pin test methods (36 equality comparisons — ticket said 37, actual count is 32/36); 6 empty sentinel headings (5× `## Reference boundary`, 1× `## Consumer reach`). inline

- Q1: release-tag hazard **restated on standalone grounds**, agentflow rationale dropped. Why: repo has a published release (v0.1.0) and the operator's work profile has a release-creating skill; tags remain consumable published history. inline
- Q2: **evidence v2 fully removed** — the Evidence v2 sections in code-review, plan-review, orchestrate, and scope SKILL.md; the `docs/evidence/` tree; validate.py's contract/provenance/envelope checks; the spec/project claims. Why: emission is write-only — the only reader (agentflow's daemon) is gone; nothing in-repo consumes an envelope. Operator widened scope to include skill-behavior changes. The future reviewer-memory consumer is preserved as its own design, not by keeping dead format. → issue (#197 filed)
- Q3 (default, unasked): pin tests — file-to-file cross-copy checks survive (they protect live duplication in interactive use); test-constant byte pins convert to structural property checks (heading exists, section non-empty, named consumer) or are deleted with their sentinel headings. Why: the ticket's done-when states it. inline

## Open questions

(none)

## Spawned tasks

- #196 filed: codex-worker.py effort enum mismatch (found during this session's headroom probe, unrelated to 195).
- #197 filed: per-repo reviewer memory idea (future consumer for evidence-like records; new design, own reader).
