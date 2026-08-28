# Tasks

## Independent baseline work

- [x] [#221](https://github.com/ConnorGriffin/skills/issues/221) Reformat and
  backfill the three baseline specs into the
  CLI-enforced shape, correcting them against current source. Landed in #227;
  `openspec validate --specs --strict` now reports 3 passed, 0 failed.

## v1.x migration

- [x] [#222](https://github.com/ConnorGriffin/skills/issues/222) Migrate the
  OpenSpec tree through `openspec init --tools
  none`, move useful `project.md` content to `config.yaml`, and remove the
  legacy files. Landed in #226. This also discharged the charter ADR-home
  contradiction, which lived in the deleted `openspec/AGENTS.md`.

- [ ] [#228](https://github.com/ConnorGriffin/skills/issues/228) Adopt the CLI
  as development and CI tooling, including a
  strict-validation gate in `.github/workflows/validate.yml`. Unblocked.

- [ ] [#229](https://github.com/ConnorGriffin/skills/issues/229) Rework
  `openspec-adopt` to scaffold through `openspec
  init` rather than by hand. Unblocked. Shares
  `skills/drivers/openspec-adopt/` with #230; sequence them.

- [ ] [#231](https://github.com/ConnorGriffin/skills/issues/231) Drop
  `ledger.md` from the `epic` skill and use the vanilla
  tracker-linked `tasks.md` shape. Unblocked. #218 already runs this way, so it
  is the worked example.

- [ ] [#230](https://github.com/ConnorGriffin/skills/issues/230) Switch the
  pack to post-merge OpenSpec archiving across
  `epic`, `ticket`, and `openspec-adopt`. Blocked by #231, which removes the
  standing planning pull request the current archiving rule depends on.
