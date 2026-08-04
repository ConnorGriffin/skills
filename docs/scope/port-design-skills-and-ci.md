# Scope ledger — port design skills & CI design

Routed: scope → interview mode (2026-08-04). Plan: port vendored `codebase-design`
and `domain-modeling` into this repo with improvements; new concern: CI is noisy
and possibly inefficient, maybe warranting a "CI design" counterpart.

## Decisions

- CI scope is the agentflow fleet repos' PR CI, not this repo alone. (why: that's
  where CI runs constantly and noise costs the most) — inline
- CI deliverable: audit the fleet CI first, then distill findings into a new
  `ci-design` skill — the skill is the end goal, the audit grounds it. — inline
- Port posture: rework both skills to charter voice/conventions during the port,
  not verbatim-then-iterate. — inline
- Ported ADR-FORMAT.md is rewritten to the charter's `adr-<issue>-<slug>.md`
  scheme; sequential numbering documented only as legacy. (why: two documented
  formats invites agents to follow the wrong one) — inline
- DESIGN-IT-TWICE keeps the portable "spawn 3+ sub-agents" wording, plus a line:
  under coordinator mode, route the fan-out per orchestrate's routing table
  (brainstorming row). — inline
- DESIGN-IT-TWICE becomes offerable mid-interview when interface shape hits the
  frontier, like `ground it`; standalone invocation unchanged. — inline
- CI "noise" priorities: billing/minutes waste first, then slow PR feedback,
  then run/notification volume. Flaky-red-runs not a felt pain. — inline
- Mechanical defaults accepted: frontmatter cross-dependency; glossary→CONTEXT.md
  vs decision→ledger split line; charter paraphrase kept, skill canonical. — inline

- Port enactment confirmed; built by implementation tier, verified, merged to
  main (c1afee3, 907100d). Symlinked via install.sh (Claude + Codex); vendored
  sources deleted; dotfiles PUBLISHED_SKILLS updated (9216202). Done. — inline
- Path filters fleet-wide, required-checks-safe pattern. (why: biggest minutes
  lever; billing is top pain) — → issue
- Brewgen CodeQL moves off per-PR to scheduled + main pushes. — → issue
- Homelab Ansible test ported off macOS runner to ubuntu. — → issue
- agentflow duplicate `dynamic` check runs: ground-it investigation dispatched
  before deciding the fix. — inline
- Fixes ship as one `ready-for-agent`-labeled issue per fleet repo. Filed:
  dotfiles#61, ciq-autotune#554, homelab#49, Brewgen#86, agentflow#514
  (path filters + CodeQL export). — → issue (5/5 discharged)
- Ground-it verdict: agentflow's duplicate check set is GitHub's hosted CodeQL
  default setup (repo settings, weekly, no yml on disk) — not the daemon, and
  not duplicated work; it's security scanning invisible to workflow-file
  audits. — inline
- Cross-cutting mechanical fixes fold into the same issues: concurrency-cancel
  groups where missing (dotfiles, homelab), Playwright caching (ciq-autotune).

- agentflow: export CodeQL default setup to a checked-in
  `.github/workflows/codeql.yml` ("switch to advanced") — visible,
  version-controlled, consistent with Brewgen's scheduled-scan decision; fold
  into agentflow's CI issue with the path filters. — → issue
- `ci-design` skill shape: vocabulary SKILL.md + audit playbook as a reference
  file, mirroring the repo's skill layout; grounded in the 2026-08-04 fleet
  audit. Built, verified, merged (dd9ace0), published via install.sh (a5d67ff).
  — inline

## Exit

All dispositions discharged 2026-08-04: 5 fleet issues filed, both ports and
the ci-design skill merged + published. Session complete. Repos not pushed.

## Open questions

(none — frontier empty)

- (blocked on CI audit) which systemic CI issues are real, what the fixes are,
  and what the distilled `ci-design` skill's shape should be.

## Exploration findings (sub-agent, 2026-08-04)

- Zero Matt-Pocock-specific references in either skill; self-contained; straight
  copy into `skills/<name>/` works with no path rewrites.
- Charter already cites codebase-design's vocabulary near-verbatim (drift risk
  between the two copies).
- scope/interview.md, tdd, and wayfinder already reference both skills — the
  port fills dangling references rather than adding new surface.

## Spawned tasks

- Explore agent: skill port analysis — done, findings above.
- Explore agent: fleet CI noise/efficiency survey — running.
