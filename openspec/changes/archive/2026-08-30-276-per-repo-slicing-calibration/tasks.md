# Tasks

- [x] Make `finalize`'s misprediction path report-only, with no rubric diff, no pull request, and no operator prompt.
- [x] Restate the report-only contract in `ticket/SKILL.md` and `docs/epic-flow.md`.
- [x] Delete the anchor table from `references/slicing.md` and point its provenance at the per-repo store.
- [x] Make `triage` read the reviewer-memory store as the anchor source and record which anchor matched.
- [x] Update the work-order template's "Why sliced" placeholder.
- [x] Pin the new contract in tests and repoint the section splits that keyed on the anchor table.
- [x] Record the decision as an ADR and modify the two affected spec requirements.
- [x] Migrate repo-attributed anchor rows into their reviewer-memory slicing digests.
- [x] Run the repository gate and record its result in the pull request.
