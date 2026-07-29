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
- **`grilling`:** sharpens the UI brief. Without it, run the short inline
  interview described by `ui-mockups`.
- **`codebase-design`:** helps shape non-trivial render logic. Without it, keep
  the shipping module shape and preserve locality.
- **`impeccable`:** adds a final visual-quality audit. Without it, run the
  explicit contrast, focus, overflow, and target-size checks.

Install Matt Pocock's optional skills from their owner rather than copying them
into this pack:

```sh
npx skills add mattpocock/skills --skill grilling --skill codebase-design
```

## Development

Run the repository checks with:

```sh
python3 scripts/validate.py
```

Contributions require a Signed-off-by trailer under the
[Developer Certificate of Origin](CONTRIBUTING.md#developer-certificate-of-origin).

## License and support

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Security reports belong
in the private channel described in [SECURITY.md](SECURITY.md); everything else
uses GitHub issues.
