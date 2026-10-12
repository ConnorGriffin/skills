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
- [ ] Rewrite the ticket skill: fold scope and preflight into triage, drop the
      graph-identity rule and orchestrate references, and update the
      ticket-workflow `Four-verb lifecycle` requirement that still names `/scope`.
- [x] Run `openspec validate --all --strict`, `python3 scripts/validate.py`, and the
      behavior suites from `.github/workflows/validate.yml`.
