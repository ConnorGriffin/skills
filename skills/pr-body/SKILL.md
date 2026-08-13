---
name: pr-body
description: Write a pull-request body and score it before the PR is opened, or audit an existing PR's body against the same rubric. Use when about to run gh pr create, when a PR body needs writing or rewriting, or when asked whether a PR description is any good. Invoked as /pr-body write <body-file> or /pr-body audit <pr>.
---

# PR body

The body is for whoever merges the change. It carries facts about the change in
the system's own terms. The diff already carries the files.

Start from a real one. A Pulumi PR that grows a GHES appliance data volume:

```markdown
Grows the appliance data volume from 2 TB to 4 TB. It has been
running near capacity.

* Volume size 2000 to 4000 GiB.
* Resources: 1 to update.

EBS expands online. The filesystem grows on the next boot.

This PR was written in part with the assistance of generative AI.
```

No headings. No reason the author does not actually know. No advice for the
reviewer. Nothing that rates the change. Everything below is that example,
generalized.

## The shape

1. **Open with the action, and put the situation behind it.** "Grows the volume
   from 2 TB to 4 TB. It has been running near capacity." The situation is
   support for the action, not a runway to it.
2. **Never invent the motivation.** Write only what you know. "Before the next
   release cycle" is an assumption dressed as a fact, and a reviewer who knows
   the schedule will spot it. If nobody told you why, the body says what
   changed and stops.
3. **Flat bullets, at the level of behavior.** No `Summary` / `Changes` /
   `Testing` scaffolding you invented. If the repo ships a PR template, fill its
   sections; if it does not, the body has no headings.
4. **One bullet per genuinely distinct fact.** Three bullets that restate each
   other are one fact and two lines of padding. Never a bullet per file.
5. **Evidence is the raw number, not the method.** `Resources: 1 to update`
   beats a sentence about running preview against dev and prd. The reader wants
   the result; the method is the author's business.
6. **Risk is the one place prose belongs, and only the mechanism half.** "EBS
   expands online, no downtime." State how the system behaves. Do not rate the
   change.
7. **Say nothing to the reviewer.** No "worth checking", no "please review the
   IAM change". Telling a reviewer where to look is telling them where not to.
8. **Length follows the facts.** One line when there is no risk and no context
   worth stating. Longer when a change carries three genuine risks. There is no
   target and no ceiling. A body is as long as the true statements about the
   change and no longer.

## Textures to cut

* **Verdict clauses.** "This is a low-risk change", "no downtime is expected",
  "improves maintainability", "should have no impact". These rate the change
  instead of describing it, and every one of them is a claim the reader cannot
  check. Banned as a class, not as a wordlist.
* **Parenthetical asides.** One per body at most. Past that they read as an
  author arguing with themselves.
* **Inline code spans and symbol names.** Name the behavior. A function name in
  prose sends the reader to the diff to find out what the sentence meant.
* **Paragraphs where bullets serve.** If it is a list of facts, make it a list.
* **Prose volume with no action behind it.** Three paragraphs on a two-line
  change is the most common failure in the labeled set.
* **Pretentious or juvenile phrasing.** Write the plain sentence.
* **An em dash** (use parens or two sentences), **emoji**, `-` bullets, and
  capitalized host or resource names.

## Before and after

Invented motivation, and the action buried:

> As part of our ongoing capacity work ahead of the Q3 release, and because the
> appliance has been under pressure for some time, this PR increases the data
> volume.

Becomes:

> Grows the appliance data volume from 2 TB to 4 TB. It has been running near
> capacity.

Invented scaffolding, and a bullet per file:

> ## Summary
> ## Changes
> * `pulumi/volumes.go`: change size
> * `pulumi/Pulumi.prd.yaml`: bump config
> ## Testing
> Ran preview.

Becomes:

> Grows the appliance data volume from 2 TB to 4 TB.
>
> * Resources: 1 to update.

Verdict and method narration, replaced by mechanism and number:

> This is a low-risk change and should have no impact. I verified it with
> pulumi preview against dev and prd.

Becomes:

> EBS expands online. The filesystem grows on the next boot.
>
> * Resources: 1 to update.

## Verbs

### write

Score a body file, run the judge, and write a receipt on pass. This is the path
the hook requires.

1. Write the body to a file. The hook only reads `--body-file`, so the file has
   to exist anyway.
2. Run the scorer against it, with the target repo so it can read the repo's PR
   template:

   ```sh
   python3 <pr-body-skill-directory>/scripts/pr_body_lint.py \
     --body-file <path> --repo <repo-root> --json
   ```

3. Fix every blocking finding. Each one carries fix text written as an
   instruction; apply it to the body, do not argue with it. A warning is a
   judgment call the author owns.
4. Run the voice judge over the fixed body: [references/judge.md](references/judge.md).
   Give it the body and the diff (`git diff <base>...HEAD`), which the judge
   needs to see a fact the change makes load-bearing that the body never
   mentions. The judge returns a verdict plus line-level rewrites, some of them
   lines to add. Apply the rewrites you accept, then re-run the scorer, because
   a rewrite can reintroduce a rule finding.
5. On a clean scorer pass and a judge pass, write the receipt: the sha256 of the
   body file's exact bytes, at
   `~/.local/state/pr-body/receipts/<sha256>.json`. Then open the PR with
   `--body-file` pointing at the same file.

Editing the file after step 5 changes its hash and voids the receipt. Run the
write verb again.

### audit

Score an existing PR's body and report. Never modify it.

1. Pull the body to a file: `gh pr view <pr> --json body -q .body`.
2. Run the scorer against it, with `--repo` pointed at a checkout of the target
   repo.
3. Run the judge over the same body, with `gh pr diff <pr>` as the diff.
4. Report the scorer findings by rule with their line numbers, then the judge's
   rewrites. No receipt is written, because the audit did not author the body.

## The gate

A PreToolUse hook on `Bash` matches `gh pr create` and `gh pr edit`, hashes the
`--body-file` it was handed, and hard-denies when no receipt matches that hash.
It also denies the invocation forms it cannot read (inline `--body`, heredocs),
which is what forces `--body-file` in the first place.

**There is no bypass.** No environment variable, no marker line, no flag. An
agent that reaches the deny has one move: fix the body and run the write verb.
The escape that does exist is uninstalling the hook from `~/.claude/hooks/`,
which a human can do and an agent must not.

The hook fails closed. An internal error, a malformed payload, or an unreadable
body file all deny. The asymmetry that justifies it: a human can uninstall the
hook, an agent cannot, so a broken gate costs a human one edit and costs an
agent nothing it should have had.

## What the gate cannot see

The deterministic scorer catches roughly a third of what the operator rejects.
On the hand-labeled set of 25 real bodies it caught 4 of the 12 rejected ones,
and all 4 were empty or near-empty. Every miss was a voice judgment:
pretentious phrasing, too much prose for not enough action, too many
parentheses, too many code references.

That is the whole reason the judge exists, and the reason a receipt (rather than
a lint exit code) is what the hook checks. A body that passes the linter has
been checked for countable defects only. Do not read a pass as a verdict that
the body is good.

## Rules the scorer implements

`scripts/pr_body_lint.py` is the only rule engine. A rule named here and absent
there is decorative. Grounds and fix text for each:
[references/rubric.md](references/rubric.md).

| Rule | Fires on | Severity |
| --- | --- | --- |
| `empty-body` | a body with no non-whitespace content | blocks |
| `ai-disclosure-missing` | no line disclosing AI assistance | blocks |
| `empty-template-section` | a heading with nothing under it | blocks |
| `vacuous-opener` | a first line like "Fix bug", "Phase 1", "Cleanup" | blocks |
| `oversized-input` | input past the scorer's robustness cap | blocks |
| `em-dash` | an em dash in prose | blocks |
| `emoji` | an emoji codepoint in prose | blocks |
| `path-in-prose` | a file path outside code formatting | blocks |
| `method-narration` | "verified with", "I ran", "tested by running" | blocks |
| `verdict-clause` | a clause rating the change instead of describing it | blocks |
| `reviewer-instruction` | "please review", "worth checking", "take a look at" | blocks |
| `bullet-per-file` | most bullets in a list of 3 or more lead with a filename | blocks |
| `symbol-in-prose` | an identifier or function name outside code formatting | warns |

Two behaviors of the scorer are worth knowing before arguing with a finding.
Lines matching the repo's `.github/pull_request_template.md`, and the AI
disclosure line, are treated as scaffolding and exempt from the prose rules.
Below 40 characters of prose the density rules (em dash, emoji, paths,
narration, verdicts, reviewer asks, bullet-per-file, symbols) do not run at all;
the structural rules run at every length.
