---
name: pr-body
description: Write a pull-request body and score it before the PR is opened, or audit an existing PR's body against the same rubric. Use when about to run gh pr create, when a PR body needs writing or rewriting, or when asked whether a PR description is any good. Invoked as /pr-body write <body-file> or /pr-body audit <pr>.
---

# PR body

The body is for whoever merges the change. It carries facts about the change in
the system's own terms. The diff already carries the files.

## The gold standard

This is the target. Copy its shape, not its subject.

The whole thing is what you would say to the team in one sentence, plus the
handful of facts a merger cannot get from the title. The decisions, the
alternatives, and the operator log are in the diff and the spec, and the body
says where they are rather than repeating them.

```markdown
## Motivation and Context

ghes-config now sets the memory ceilings and rate-limit posture that production already runs: 17 keys per ring for prd and stg, read off the production primary, rate limiting off. Staging had sandbox-sized ceilings on production-sized hardware.

* The 14 rate-limit keys are new to the reconciler's allowlist, on the `ghe-config` transport. dev.yaml is unchanged.
* Staging's primary was brought to those values by hand. Three of the four keys written did not exist there before, so the comparison below shows staging carrying production's values, not the appliance honouring the new ceilings.
* No reconciler instance exists in any ring, so nothing reads these files today.

Decisions and the operator log are in the change folder under `openspec/changes/archive/`.

Fixes PROJ-7351

## How Has This Been Tested?

* Production primary against staging primary after the apply: 17 lines per side, diff exit 0. Replication in sync on both replicas.
* `parity_test.sh` 37 checks pass, `python3 -m unittest discover -s scripts` 36 OK.
* `pulumi preview` against `origin/main`: this branch moves no resource.

## Checklist before requesting a review

- [x] I have performed a self-review of my code.
- [x] I have stepped through the README as though I was a new user to ensure clarity.
- [ ] I have added new or changed keys, tokens, other secrets to the DevOps 1Pass.
- [ ] I have labeled all "TO DO" items with associated Jira ticket number.
- [x] I have removed commented code from PRs to `main`.
- [x] I have followed conventional-commits standards when making this PR.

> Written by an AI agent operating for <operator>. Verify before relying on it.
```

## What that body does

1. **Sections come from the team, never from you.** Fill
   `.github/pull_request_template.md` when the repo ships one, then the
   organization default in the organization's `.github` repo. When neither
   exists, read the last two merged pull requests written by someone else and
   use their headings; a team convention lives in the pull requests even when it
   lives in no file. Only a repo with no template and no history gets a body
   with no headings.
2. **The opening states what the system now does**, present tense, then the
   state it replaced. One sentence each. It is the line you would say to the
   team, and a reader who stops there has the change.
3. **Three or four bullets, not twelve.** A bullet earns its place by carrying a
   fact the opening does not imply. Never a bullet per file, and two bullets
   that restate each other are one bullet.
4. **Point at the spec and the diff instead of summarizing them.** Why this
   value, what else was considered, which command ran in what order: one line
   saying where that lives. A reader who wants the decision opens the spec, and
   a body that retells it goes stale against it.
5. **Evidence is the raw number.** "17 lines per side, diff exit 0", "37 checks
   pass", "moves no resource". Not the method, not the command line, not a
   sentence about having been careful.
6. **The caveat states what the evidence does not show.** "The comparison shows
   staging carrying production's values, not the appliance honouring the new
   ceilings." That clause is the most valuable one in the body, and it is the
   first one a weaker author drops. Fold the deviation that caused it into the
   same bullet.
7. **Blast radius as mechanism.** "No reconciler instance exists in any ring, so
   nothing reads these files today." Never a rating of the risk.
8. **`Fixes <KEY>` on its own line**, and the ticket appears nowhere else.
9. **Tick only what is true.** An unticked box for a check that does not apply
   is correct, and it is more credible than a body where every box is ticked.
10. **Length follows the facts, and most facts are not the body's job.** The
    gold standard is about 1.5 KB. An earlier draft of the same change ran 2.4
    KB by carrying decisions the spec already held, and prose ran 5.8 KB and
    said no more.

## Never

* Motivation nobody told you. "Ahead of the next release cycle" is a guess
  wearing a fact's clothes.
* A clause that rates the change: "low risk", "no impact expected", "improves
  maintainability", "lands cleanly". The reader can check a mechanism and cannot
  check a rating.
* Anything addressed to the reviewer: "worth checking", "please look at the IAM
  change". Telling a reviewer where to look tells them where not to.
* Method narration: "I ran preview against dev and prd", "verified with".
* A retelling of the spec or the diff: the reasoning behind a value, the
  alternatives weighed, the order the commands ran in. Name where it lives.
* An empty template section. Cut the heading only if the template does not ship
  it; otherwise fill it.
* An em dash (use parens or two sentences), emoji, `-` bullets, capitalized host
  or account names, and a bare file path outside code formatting.
* Three parentheses in a sentence. One in a body is fine.

## Verbs

### write

1. Write the body to a file. The gate only reads `--body-file`, so the file has
   to exist anyway. Pass an absolute path with no `~`: the gate reads the
   command text, and it cannot resolve a tilde or a path that does not exist
   yet. Create the file in one call and run `gh` in the next, or the gate sees a
   file that is not there.
2. Score it, with the target repo so the scorer can read the repo's template:

   ```sh
   python3 <pr-body-skill-directory>/scripts/pr_body_lint.py \
     --body-file <path> --repo <repo-root> --json
   ```

3. Fix every blocking finding. Each carries fix text written as an instruction;
   apply it rather than arguing with it. A warning is a judgment call you own.
4. Run the voice judge: [references/judge.md](references/judge.md). Give it the
   body and `git diff <base>...HEAD`. The judge exists for one thing the scorer
   cannot see: a fact the diff makes load-bearing that the body never mentions.
   Apply the rewrites you accept, then re-score, because a rewrite can
   reintroduce a rule finding.
5. Record the receipt, then open or edit the pull request with `--body-file`
   pointing at the same file:

   ```sh
   python3 <pr-body-skill-directory>/scripts/pr_body_receipt.py write <path>
   ```

Editing the file after step 5 changes its hash and voids the receipt. Run the
write verb again.

### audit

Score an existing body and report. Never modify it.

1. `gh pr view <pr> --json body -q .body > <path>`.
2. Score it with `--repo` pointed at a checkout of the target repo.
3. Run the judge over the same body, with `gh pr diff <pr>` as the diff.
4. Report the scorer findings by rule with their line numbers, then the judge's
   rewrites. No receipt: the audit did not author the body.

## The gate

A separately installed PreToolUse hook on `Bash` matches `gh pr create` and `gh pr edit`, hashes the
`--body-file` it was handed, and denies when no receipt matches that hash. It
also denies the forms it cannot read: inline `--body`, heredocs, a tilde path, a
file that does not exist yet.

When that hook is installed, there is no bypass and it fails closed. The escape that exists is
uninstalling the hook from `~/.claude/hooks/`, which a human can do and an agent
must not.

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

Lines matching the repo's template, and the AI disclosure blockquote, are
scaffolding and exempt from the prose rules. Below 40 characters of prose the
density rules do not run at all; the structural rules run at every length.

A scorer pass means the countable defects are absent. On the labeled set it
caught 4 of 12 rejected bodies, and all 4 were empty or near-empty. Everything
else was voice, which is what the judge and the gold standard above are for.
