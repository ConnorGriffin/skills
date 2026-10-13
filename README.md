# Connor Griffin's agent skills

A portable skill pack for coding agents. Skills live under [`skills/`](skills/)
and work with clients that support the Agent Skills format. Each skill files under
one of two categories: `drivers` (multi-phase procedures chosen deliberately, which
call other skills by name) and `tools` (skills that do one job themselves). Some
skills compose: `ticket` calls `plan-review` and `code-review` at its gates.

Browse the pack at <https://connorgriffin.github.io/skills/>.

## Included skills

### Drivers

| Skill | Purpose | Extra requirement |
| --- | --- | --- |
| [`implement`](skills/drivers/implement/SKILL.md) | Routes tracked work through `ticket`; gives an explicit isolated-worktree intake for an untracked PRD | `ticket` and `code-review` from this pack |
| [`openspec-adopt`](skills/drivers/openspec-adopt/SKILL.md) | Initialize the OpenSpec v1 layout and baseline specs describing the system today, delivered as a documentation-only PR | GitHub CLI; global `@fission-ai/openspec@1.11.0` |
| [`ui-craft`](skills/drivers/ui-craft/SKILL.md) | Structure first, then component-grain design: inventory, a library reviewed in small batches, screens composed from approved components and locked one page in the repo; build or revise in a separate ticket; review rendered UI | Claude Code's Design and Design System artifact types, or plain artifacts, for canvases; Claude in Chrome or the built-in browser for rendered checks; subagent support for the cold critique |
| [`ticket`](skills/drivers/ticket/SKILL.md) | Drive one tracked ticket through four verbs, one artifact each with a human gate between: triage resolves open questions and locks a work order on the ticket, start builds it to an open pull request, revise actions one review round, finalize closes it after a human merges and records what it cost. Agents never merge | GitHub CLI for the bundled issues binding, one binding page per other tracker; composes with `plan-review`, `code-review` |

### Tools

| Skill | Purpose | Extra requirement |
| --- | --- | --- |
| [`ci-design`](skills/tools/ci-design/SKILL.md) | Vocabulary and principles for well-designed CI | — |
| [`code-review`](skills/tools/code-review/SKILL.md) | Review changes since a fixed point on two axes, Standards and Spec, each returning a verdict per enumerated item so a round terminates | Parallel-agent support recommended; GitHub CLI to fetch an originating issue; see [docs/review-round-mining.md](docs/review-round-mining.md) for the mined evidence behind the fix protocol and the round cap |
| [`codebase-design`](skills/tools/codebase-design/SKILL.md) | Shared vocabulary for designing deep modules | — |
| [`domain-modeling`](skills/tools/domain-modeling/SKILL.md) | Build and sharpen a project's domain model | — |
| [`handoff`](skills/tools/handoff/SKILL.md) | Produce a decision-safe handoff for a fresh agent | — |
| [`plan-review`](skills/tools/plan-review/SKILL.md) | Adversarially review a plan or work order with cold agents before building | Parallel-agent support recommended; the round-count evidence behind its rules is in [docs/review-round-mining.md](docs/review-round-mining.md) |
| [`prototype`](skills/tools/prototype/SKILL.md) | Build a throwaway prototype — a terminal app for logic questions or switchable UI variants in the real app | — |
| [`research`](skills/tools/research/SKILL.md) | Investigate a question against primary sources and capture findings as Markdown in the repo | — |
| [`say-less`](skills/tools/say-less/SKILL.md) | Answer-first output shaping with a per-repo glossary of approved terms; adapted from i-have-adhd, merged with this pack's reader-preference rules and an ASD-STE100 subset | Optional prompt hook for always-on digest; see [docs/overlay.md](docs/overlay.md) and the [measured comparison](docs/before-after.md) |
| [`tdd`](skills/tools/tdd/SKILL.md) | Test-driven development through public interfaces, red-green-refactor | — |
| [`writing-for-agents`](skills/tools/writing-for-agents/SKILL.md) | Write or review a skill against a shared pointer/load/pruning vocabulary; `doctor` verb audits the loaded skill and `CLAUDE.md`/`AGENTS.md` estate for token cost and trigger risk | Hand-only; invoke by name |

## Install

Install one skill with the standard
[`skills` CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add ConnorGriffin/skills --skill ui-craft
```

Install several together:

```sh
npx skills add ConnorGriffin/skills \
  --skill ticket \
  --skill plan-review \
  --skill code-review
```

Install every skill:

```sh
npx skills add ConnorGriffin/skills --all
```

The CLI prompts for the target agents and whether to install per-project or
globally. Review skill instructions and scripts before running them; several
skills intentionally start processes or modify repositories.

## Optional integrations

Optional integrations are enhancements, not hidden runtime requirements. Both
ship in this pack and are optional because a partial install can leave them out:

- **`codebase-design`:** ships in this pack; referenced by `tdd`; helps shape
  non-trivial module interfaces. Without it, keep the shipping module shape and
  preserve locality.
- **`domain-modeling`:** ships in this pack; referenced by
  `codebase-design`; maintains a project's domain vocabulary. Without it, ground terms
  in the repo's own docs.

## Attribution

The `implement`, `tdd`, and `prototype` skills are adopted from — and
`code-review` is derived from — [Matt Pocock's
skills repository](https://github.com/mattpocock/skills) (MIT, copyright (c) 2026
Matt Pocock), lightly edited here to be self-contained. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).

## Output style

[`output-styles/say-less.md`](output-styles/say-less.md) is a Claude Code output
style: it replaces the built-in coding instructions so every reply leads with the
outcome and stops there. The `say-less` skill is the full ruleset for documents;
the style is the always-on subset.

Same task, same model, style the only difference. Neither reply is truncated:

![Two replies to one diagnosis task, side by side. The default style answers in
235 words across four sections; say-less answers in 56 words. Both name the
off-by-one loop, the loose assertion and the wasted backoff
sleep.](docs/img/retry-diagnosis.svg)

Both arms found the same three defects. Full text of every arm:
[`examples/transcripts/`](examples/transcripts).

Across 120 headless runs on a 10-question set with an executed answer key:

| model | median output tokens, default | say-less | outcomes correct, default | say-less |
| --- | --- | --- | --- | --- |
| claude-opus-5 | 348 | 164 | 20/20 | 10/10 |
| claude-sonnet-5 | 436 | 164 | 115/120 | 38/40 |
| claude-fable-5 | 456 | 178 | 20/20 | 10/10 |

Half to two thirds of the reading, no correctness cost on opus or fable. Sonnet
keeps one residual failure worth knowing about before you install it, and
compression drops caveats a longer reply would have kept: both are measured, with
their method and the counterexamples, in
[docs/before-after.md](docs/before-after.md).

Activate it by setting `"outputStyle": "say-less"` in `~/.claude/settings.json`
after linking the file into `~/.claude/output-styles/`, or run
`/output-style say-less` in an interactive session. New sessions pick it up; the
one you are in does not.

## Shared profile

[`profile/`](profile/README.md) holds a machine-agnostic global-instructions
layer (communication rules, working preferences, an engineering charter) meant
to be `@`-imported from a local checkout of this repo into each machine's own
`CLAUDE.md`/`AGENTS.md`, with machine-specific overlays staying private. See
[`profile/README.md`](profile/README.md) for setup.

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
