# Tasks

- [x] Remove `codebase-memory`, `cbm-onboard`, `.cbmignore`, their tests, CI lines,
      README entries, and the profile's code-discovery paragraph; mark ADR 65
      superseded.
- [x] Remove `orchestrate` and its scripts and references; move `code-review`,
      `plan-review`, `research`, and design-it-twice to native read-only subagent
      dispatch; add "Delegating to subagents" to `profile/base.md`; mark ADR 149
      and ADR 150 superseded.
- [x] Remove `persona-review`, the `personas` review route, plan-review's persona
      panel, UI Craft's `consensus` mode and `init` persona-panel step, and the
      repository hazard about colleague profiles.
- [x] Delete `scope` and `preflight`; point other skills at `/ticket triage`.
- [x] Remove the docs site nodes, edges, narratives, and mockup entries for the
      removed skills.
- [x] Rewrite the ticket skill: fold scope and preflight into triage, drop the
      graph-identity rule and orchestrate references, and update the
      ticket-workflow `Four-verb lifecycle` requirement that still names `/scope`.
- [x] Cut the ticket skill's prose under 600 lines, drop its prose-pinning tests,
      and keep the `ticket.py` CLI tests plus a small structural set.
- [x] Remove `epic`, its tests, validator and CI entries, docs guide, README, site,
      and mockup entries; mark ADR 143 superseded; record the ticket-workflow and
      planning-and-review deltas.
- [x] Remove `drive-local-webapp`, `clean`, `spin-worktree`, and the `review` front
      door with their scripts, tests, validator, CI, README, NOTICE, site, and
      mockup entries; point surviving skills at the harness browser, `/simplify`,
      a fresh worktree, `/code-review`, and `/plan-review`; mark ADR 52
      superseded; record the pack-integrity and planning-and-review deltas.
- [x] Drop `ticket.py record`'s unused chunked-order verdict and its tests.
- [x] Run `openspec validate --all --strict`, `python3 scripts/validate.py`, and the
      behavior suites from `.github/workflows/validate.yml`.
