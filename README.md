# Connor Griffin's agent skills

A portable skill pack for coding agents. Skills live under [`skills/`](skills/)
and work with clients that support the Agent Skills format. Some skills compose:
the UI workflow uses the bundled browser driver for rendered evidence.

## Included skills

| Skill | Purpose | Extra requirement |
| --- | --- | --- |
| [`ui-mockups`](skills/ui-mockups/SKILL.md) | Explore grounded UI directions and lock one visual spec before implementation | `drive-local-webapp` for rendered review; parallel-agent support is recommended |
| [`drive-local-webapp`](skills/drive-local-webapp/SKILL.md) | Drive and screenshot a local web app with headless Chromium | Node.js 20+; installs Playwright locally |
| [`cbm-onboard`](skills/cbm-onboard/SKILL.md) | Index a repository with codebase-memory-mcp and keep it current | `codebase-memory-mcp` on `PATH` |
| [`spin-worktree`](skills/spin-worktree/SKILL.md) | Create isolated Git worktrees for issue and PR work | Git; GitHub CLI only for `--pr` discovery |
| [`grilling`](skills/grilling/SKILL.md) | Relentlessly interview the user to stress-test a plan or design before building | — |
| [`wayfinder`](skills/wayfinder/SKILL.md) | Chart a large, foggy effort as a GitHub map of decision tickets, then hand clear subtrees to implementation | GitHub CLI; composes with `research`, `grilling`, `ui-mockups` |
| [`research`](skills/research/SKILL.md) | Investigate a question against primary sources and capture findings as Markdown in the repo | — |
| [`prototype`](skills/prototype/SKILL.md) | Build a throwaway prototype — a terminal app for logic questions or switchable UI variants in the real app | — |
| [`interface-craft`](skills/interface-craft/SKILL.md) | Design distinctive, production-quality web and product interfaces | — |
| [`tdd`](skills/tdd/SKILL.md) | Test-driven development through public interfaces, red-green-refactor | — |
| [`review`](skills/review/SKILL.md) | Review changed code against the project's standards and the originating issue | — |
| [`implement`](skills/implement/SKILL.md) | Implement a PRD or issue set via `tdd`, then `review`, then commit | `tdd` and `review` from this pack |

## Install

Install the primary UI workflow with its required browser driver using the
standard [`skills` CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ConnorGriffin/skills \
  --skill ui-mockups \
  --skill drive-local-webapp
```

Install another skill by itself:

```sh
npx skills add ConnorGriffin/skills --skill spin-worktree
```

Install every skill:

```sh
npx skills add ConnorGriffin/skills --all
```

The CLI prompts for the target agents and whether to install per-project or
globally. Review skill instructions and scripts before running them; several
skills intentionally start processes, modify repositories, or install Git
hooks.

## Optional upstream skills

Optional integrations are enhancements, not hidden runtime requirements:

- **Codebase Memory:** accelerates structural exploration. Without it, use
  ordinary repository search and file reads.
- **`codebase-design`:** referenced by `tdd`; helps shape non-trivial module
  interfaces. Without it, keep the shipping module shape and preserve locality.
- **`domain-modeling`:** referenced by `grilling` and `wayfinder`; maintains a
  project's domain vocabulary. Without it, ground terms in the repo's own docs.
- **`impeccable`:** adds a final visual-quality audit. Without it, run the
  explicit contrast, focus, overflow, and target-size checks.

Install Matt Pocock's optional skills from their repository:

```sh
npx skills add mattpocock/skills --skill codebase-design --skill domain-modeling
```

## Attribution

The `implement`, `tdd`, `review`, and `prototype` skills are adopted from — and
`grilling` is derived from — [Matt Pocock's skills
repository](https://github.com/mattpocock/skills) (MIT, copyright (c) 2026 Matt
Pocock), lightly edited here to be self-contained. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).

## Development

Run the repository checks with:

```sh
python3 scripts/validate.py
```

Contributions require a Signed-off-by trailer under the
[Developer Certificate of Origin](CONTRIBUTING.md#developer-certificate-of-origin).

## License and support

MIT, from v0.2.0 onward (v0.1.0 was published under Apache-2.0, and that grant
stands for copies taken at that tag). See [LICENSE](LICENSE) and
[NOTICE](NOTICE). Security reports belong
in the private channel described in [SECURITY.md](SECURITY.md); everything else
uses GitHub issues.
