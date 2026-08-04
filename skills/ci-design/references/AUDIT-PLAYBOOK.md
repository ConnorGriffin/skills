# CI Audit Playbook

The repeatable procedure for auditing one or more repos' CI, distilled from
the 2026-08-04 fleet audit. Assumes the vocabulary in `../SKILL.md`.

## Procedure

1. **Inventory the workflows.** Read every `.github/workflows/*.yml` in the
   repo. For each job, record: trigger surface (events, branches, paths),
   runner, matrix dimensions, concurrency group, caching, and any path
   filtering (workflow-level or in-job).

2. **Pull run stats.**

   ```
   gh run list --limit 50 --json name,conclusion,event,startedAt,updatedAt,displayTitle
   ```

   Compute failure rate, cancellation rate, and median duration per
   workflow. Group by day to tell a burst (many runs clustered in a short
   window, one branch) from chronic failure (spread evenly, many branches).

3. **Check for invisible checks.** Compare what's on disk against what
   actually runs:

   ```
   gh api repos/<owner>/<repo>/code-scanning/default-setup
   ```

   and the check-suites on a recent commit (`gh api
   repos/<owner>/<repo>/commits/<sha>/check-suites`) against the workflow
   files in the repo. Anything present in check-suites without a matching
   yml is invisible.

4. **Rank findings** by the priority order in `../SKILL.md`: minutes/billing
   waste first, then PR feedback latency, then run/notification volume.

5. **Ship fixes as one self-contained issue per repo.** Each issue states
   the finding, the evidence (numbers from steps 2-3), and the fix — scoped
   so it can be picked up and built without re-running the audit.

## Known failure modes

Each of these was observed at least once in the 2026-08-04 audit. Check for
all of them, not just the first one found.

- **No path filters anywhere** — every job runs on every push, regardless of
  what changed.
- **Missing concurrency groups** — stale runs queue up and finish instead of
  cancelling; `gh run list` shows 0 cancellations despite obvious push
  churn on the same branch.
- **Uncached expensive installs** — Playwright + Chromium (or an equivalent
  heavy toolchain) reinstalled from scratch every run instead of keyed on a
  lockfile.
- **Wrong runner tier** — e.g., Ansible tests pinned to `macos-latest` for a
  single temp-path assumption that's fixable on Linux.
- **Unconditional publish jobs** — an image or package pushed on every
  main-branch push regardless of whether anything relevant changed.
- **Per-PR multi-language CodeQL matrices** — full security-scan matrices
  running on every pull request instead of on a schedule plus main pushes.
- **Duplicate check sets from settings-configured default setup** —
  GitHub's UI-configured CodeQL running alongside a checked-in workflow that
  does the same thing, doubling the check count.
- **Permanent no-op jobs** — a job kept alive indefinitely only to
  detect-and-skip on every run, rather than being removed or replaced with
  in-job path filtering.
