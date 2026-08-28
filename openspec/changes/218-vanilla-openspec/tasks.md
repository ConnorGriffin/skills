# Tasks

## Independent baseline work

- [ ] [#TBD](#TBD) Reformat and backfill the three baseline specs into the
  CLI-enforced shape, correcting them against current source. This is
  independent because `openspec init` leaves `openspec/specs/` untouched.

## v1.x migration

- [ ] [#TBD](#TBD) Migrate the OpenSpec tree through `openspec init`, move
  useful `project.md` content to `config.yaml`, choose whether to select a
  tool, and remove `project.md` manually. This has no dependency; it also
  resolves the charter ADR-home contradiction because init deletes the legacy
  `openspec/AGENTS.md` that contains it.

- [ ] [#TBD](#TBD) Adopt the CLI as development and CI tooling, including a
  strict-validation gate in `.github/workflows/validate.yml`. This depends on
  the v1.x tree migration.

- [ ] [#TBD](#TBD) Rework `openspec-adopt` to scaffold through `openspec init`
  rather than by hand. This depends on the v1.x tree migration.

- [ ] [#TBD](#TBD) Update `openspec-adopt`, `epic`, `ticket`, and the v1.x
  replacement for the legacy OpenSpec instructions for post-merge archiving.
  This depends on the v1.x tree migration.

- [ ] [#TBD](#TBD) Drop `ledger.md` from the `epic` skill and use the vanilla
  tracker-linked `tasks.md` shape. This depends on the v1.x tree migration.
