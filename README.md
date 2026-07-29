# Connor Griffin's agent skills

Portable workflows for coding agents. Each skill is self-contained under
[`skills/`](skills/) and works with clients that support the Agent Skills
format.

## Included skills

| Skill | Purpose | Extra requirement |
| --- | --- | --- |
| [`ui-mockups`](skills/ui-mockups/SKILL.md) | Explore grounded UI directions and lock one visual spec before implementation | `drive-local-webapp` for rendered review; parallel-agent support is recommended |
| [`drive-local-webapp`](skills/drive-local-webapp/SKILL.md) | Drive and screenshot a local web app with headless Chromium | Node.js 20+; installs Playwright locally |
| [`cbm-onboard`](skills/cbm-onboard/SKILL.md) | Index a repository with codebase-memory-mcp and keep it current | `codebase-memory-mcp` on `PATH` |
| [`spin-worktree`](skills/spin-worktree/SKILL.md) | Create isolated Git worktrees for issue and PR work | Git; GitHub CLI only for `--pr` discovery |

## Install

Install one skill with the standard [`skills` CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ConnorGriffin/skills --skill ui-mockups
```

Install the UI workflow and its browser driver together:

```sh
npx skills add ConnorGriffin/skills \
  --skill ui-mockups \
  --skill drive-local-webapp
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

`ui-mockups` can use interviewing, design-system, and module-design skills when
they are already installed. Those are optional enhancements, not hidden runtime
requirements. Install them from their owners rather than from this repository:

```sh
npx skills add mattpocock/skills --skill grilling --skill codebase-design
```

The workflow also recognizes an installed `impeccable` skill for its final
visual-quality gate.

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
