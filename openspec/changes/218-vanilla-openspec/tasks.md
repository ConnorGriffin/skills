# Tasks

- [x] [#221](https://github.com/ConnorGriffin/skills/issues/221) Reformat and
  backfill the three baseline specs into the CLI-enforced shape, correcting
  them against current source. Landed in #227; `openspec validate --specs
  --strict` now reports 3 passed, 0 failed.

- [x] [#222](https://github.com/ConnorGriffin/skills/issues/222) Migrate the
  OpenSpec tree through `openspec init --tools none`, move useful `project.md`
  content into `config.yaml`, and remove the legacy files. Landed in #226. This
  also discharged the charter ADR-home contradiction, which lived in the
  deleted `openspec/AGENTS.md`.

- [ ] [#228](https://github.com/ConnorGriffin/skills/issues/228) Finish the
  adoption in one pass: the deterministic CI gate, `openspec-adopt` scaffolding
  through `openspec init`, post-merge archiving across `epic`, `ticket`, and
  `openspec-adopt`, and dropping `ledger.md` from the `epic` skill. Chunked at
  triage if it needs slicing.

Filed separately and superseded by #228: #229, #230, and #231, each closed as
not planned. They split the same work by decision number, which forced three
issues to edit overlapping skill files and serialize against each other. Work
too large for one context is sliced into sub-orders inside one work order, not
into separate issues.
