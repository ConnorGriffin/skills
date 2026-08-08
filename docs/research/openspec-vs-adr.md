# OpenSpec versus an ADR-only workflow

## Verdict

**Recommendation — adopt OpenSpec selectively, not broadly.** Keep ADRs as the durable record for load-bearing architectural decisions. Use OpenSpec for AI-assisted changes that need an agreed behavior, technical approach, implementation checklist, and reviewable change history—especially cross-cutting or multi-repo work. Keep ADR-only for small changes where that planning package would cost more than it returns.

This is an inference from the documented roles of the two practices: an ADR captures one architectural decision and its rationale, trade-offs, and consequences, while OpenSpec organizes a proposed behavior change through implementation and archival.[ADR organization](https://adr.github.io/)[OpenSpec concepts](https://openspec.dev/docs/overview)

## What OpenSpec does

### Lifecycle

1. **Initialize.** Install the global CLI, then run `openspec init`; initialization creates the `openspec/` structure and AI-tool integration files. OpenSpec requires Node.js 20.19.0 or newer.[Installation](https://openspec.dev/docs/installation)[CLI source documentation](https://github.com/Fission-AI/OpenSpec/blob/main/docs/cli.md)
2. **Explore or propose.** `/opsx:explore` is optional. `/opsx:propose` creates a change and drafts the default planning artifacts: `proposal.md` (why and scope), delta `specs/` (what behavior changes), `design.md` (how), and `tasks.md` (implementation steps). The artifacts are dependency-ordered, but OpenSpec describes those dependencies as enablers rather than irreversible phase gates.[OPSX workflow](https://openspec.dev/docs/opsx)[Core concepts](https://openspec.dev/docs/overview)
3. **Review and iterate.** The change folder is a reviewable package. Artifacts may be edited and revisited as understanding changes; the team guide recommends reviewing proposal, delta spec, then code in a pull request.[Team workflow](https://openspec.dev/docs/team-workflow)[Core concepts](https://openspec.dev/docs/overview)
4. **Implement.** `/opsx:apply` works through the task list; the expanded workflow also offers `/opsx:verify` to check that implementation matches the specs.[How commands work](https://openspec.dev/docs/how-commands-work)[Examples](https://github.com/Fission-AI/OpenSpec/blob/main/docs/examples.md)
5. **Validate.** `openspec validate` checks change/spec structure and checks modified requirements against the main specs. It supports validating all changes/specs, strict mode, JSON output, and CI-friendly non-interactive operation.[CLI validation reference](https://openspec.dev/docs/reference/cli)
6. **Archive.** `openspec archive` validates by default, confirms, merges active deltas into `openspec/specs/`, and moves the completed change to `openspec/changes/archive/YYYY-MM-DD-<name>/`. The archived folder retains proposal, design, tasks, and delta specs.[CLI archive reference](https://openspec.dev/docs/reference/cli)[Concepts: archive](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)

### Tasks and change history

OpenSpec's documented to-do list is the checked-in `tasks.md` artifact inside each active change; `apply` uses it as the implementation checklist, and `status` reports artifact readiness rather than claiming that implementation tasks are complete. Active changes can be listed with `openspec list`, inspected with `show`, and viewed in a terminal dashboard.[CLI workflow reference](https://openspec.dev/docs/reference/cli)

Its change history is the dated archive of whole change folders, not merely a list of decisions. The archive preserves why (`proposal.md`), how (`design.md`), what changed (`specs/`), and the work checklist (`tasks.md`), while the main `openspec/specs/` tree becomes the current behavioral source of truth.[Concepts: archive](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)

### Archival timing and merge behavior

OpenSpec has an explicit archive command, but it does **not** impose one universal pre-merge policy. Its team guidance recommends archiving after the pull request merges, so shared specs advance only for shipped work; it also documents archiving inside the pull request as a valid, noisier alternative. The repository/team must choose and consistently enforce that convention.[OpenSpec on a team](https://openspec.dev/docs/team-workflow)

That distinction matters: OpenSpec supplies the archive operation and its validation/spec-merge mechanics; Git branching, pull-request merge order, and any “archive before merge” gate remain repository process. The docs say stores are ordinary Git repositories and OpenSpec does not clone, pull, or push automatically.[Stores](https://openspec.dev/docs/stores)

## What it adds beyond an ADR

| Need | ADR-only workflow | OpenSpec |
| --- | --- | --- |
| Durable architectural decision | Native purpose: one decision with rationale, trade-offs, and consequences; a collection forms a decision log.[ADR organization](https://adr.github.io/) | Not its primary documented role. Its proposal/design can carry reasoning, but the default workflow is a change package.[OPSX workflow](https://openspec.dev/docs/opsx) |
| Behavior/acceptance agreement | Possible, but depends on each ADR template and author | First-class requirements and concrete scenarios in delta specs.[Core concepts](https://openspec.dev/docs/overview) |
| Implementation plan | Not inherent to the ADR format; use another tracker/document if needed | First-class `tasks.md`, consumed by `apply`.[CLI reference](https://openspec.dev/docs/reference/cli) |
| Reviewable change context | Usually distributed across ADR, issue, PR, and chat by convention | One change folder groups proposal, specs, design, and tasks; the team guide places that package in the PR review order.[Team workflow](https://openspec.dev/docs/team-workflow) |
| Keeping behavior current | Requires a project convention to update docs after implementation | Archive merges delta specs into the main specs and preserves the change history.[CLI archive reference](https://openspec.dev/docs/reference/cli) |

**What OpenSpec does not replace — inference.** OpenSpec does not replace tests, issue tracking, pull-request review, Git, or the durable architectural decision practice. Its own docs describe `tasks.md` and Git-backed change folders; they do not present OpenSpec as an issue tracker or as a substitute for ADRs. In this repository family, the existing charter explicitly allows the architectural decision to live in an OpenSpec change's `design.md` under an ADR heading, while preserving an established `docs/adr/` home when one already exists.[Repository charter](../../profile/CHARTER.md)

## Adoption cost and rollout

### Repository footprint

`openspec init` adds a visible `openspec/` directory with specs, changes, and configuration, plus generated skills/commands in the selected AI-tool directories. `openspec update` regenerates those integration files after CLI changes. The project config is optional but recommended; it can inject repository context and per-artifact rules, with a documented 50 KB context limit.[Existing projects](https://openspec.dev/docs/existing-projects)[How commands work](https://openspec.dev/docs/how-commands-work)[OPSX workflow](https://openspec.dev/docs/opsx)

**Inference — operational cost.** The recurring cost is more than an ADR: each qualifying change asks the team to maintain a proposal, delta spec, design, task list, validation step, and archive convention. The payoff is highest when AI-generated code or cross-cutting behavior makes an incorrect interpretation expensive. OpenSpec itself acknowledges that the overhead may not pay off for a trivial one-line fix.[Core concepts](https://openspec.dev/docs/overview)

### Migration from existing repositories

OpenSpec's brownfield guidance says not to document an existing codebase wholesale. Initialize the repo, specify the slice being changed, and let main specs grow as real changes are archived. It also recommends committing `openspec/` to Git.[Existing projects](https://openspec.dev/docs/existing-projects)

**Recommendation — migration.** Do not mass-convert existing ADRs. Preserve them as the decision history, and start OpenSpec on a small number of new, behavior-changing changes. Where a change contains a durable architectural ruling, record that ruling using the repository's ADR convention—within `design.md` only where the repository explicitly treats OpenSpec design as its ADR home.[Repository charter](../../profile/CHARTER.md)

### Multi-repo fit

For a monorepo, OpenSpec documents one root-level `openspec/` directory. For work that genuinely spans repositories, its beta **stores** feature puts specs and changes in a standalone planning repository; code repos can reference a store, and local worksets can open the planning repo alongside several code repos. Store state is shared through normal Git commits/pushes/pulls, while registry and workset state remains machine-local.[Existing projects](https://openspec.dev/docs/existing-projects)[Stores](https://openspec.dev/docs/stores)

**Inference — risk.** Stores are promising for a multi-repo setup, but their beta status and explicit “no sync” behavior make them a poor reason to standardize OpenSpec across every repository immediately. Pilot one shared planning repo only where a real cross-repo change justifies it; otherwise keep each repo's planning local.[Stores](https://openspec.dev/docs/stores)

## Decision criteria

Choose **ADR-only** when most work is small, local, behaviorally obvious, or already tracked well elsewhere; create an ADR only when the change contains a durable architectural decision.

Choose **OpenSpec for selected changes/repos** when at least one of these is true: AI will implement a non-trivial change; acceptance behavior needs explicit scenarios; several contributors or repositories must agree on the same plan; or the implementation needs a reviewable checklist and preserved change context. Keep ADR capture inside that workflow for architectural rulings.

Choose **OpenSpec broadly** only after a pilot demonstrates that teams consistently complete and archive changes, the added review surface is useful, and the repository can enforce the chosen post-merge or in-PR archive convention. Broad rollout is especially premature if the main motivation is stores: the official guide labels stores beta.[Stores](https://openspec.dev/docs/stores)

### Bottom line

For these repositories, the practical default is **ADR-only for ordinary work, OpenSpec for selected AI-assisted or cross-cutting changes, and no broad stores rollout yet**. OpenSpec is a delivery/planning layer that complements an ADR decision log; it is worthwhile where the cost of an ambiguous plan or stale behavioral contract exceeds the cost of maintaining the extra artifacts.

## Source limits

This report uses first-party OpenSpec and ADR sources plus the repository charter. It does not claim measured productivity or adoption ROI; validate the recommendation with a small pilot. The cross-repo stores guidance is explicitly beta and may change between releases.[Stores](https://openspec.dev/docs/stores)
