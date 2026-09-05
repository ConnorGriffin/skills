# pr-body rubric

One entry per rule `../scripts/pr_body_lint.py` implements. That file is the
only rule engine; this one records what each rule fires on, what its fix says,
and what grounds it. Corpus rates are AI-era (n=100) against human-era (n=109)
merged PRs from the operator's own history. Labels are the hand-labeled set of
25 bodies the operator judged blind.

The corpus is one author's, and the labels are one author's. A rule grounded
only in "elicited" is a preference this pack encodes on purpose, not an
industry standard. Where a standard says otherwise, see *Known disagreements*.

## Rules

### `empty-body` (block)

**Fires on** a body with no non-whitespace content at all.

**Fix** State what changed and why; an empty body tells the reviewer nothing.

**Grounds** Corpus: 33 empty bodies, all human-era. Labels: every empty or stub
body in the sample was rejected. Shopify's review guide treats an inadequate
description as grounds to send the PR back before judging the code at all
(https://shopify.engineering/great-code-reviews).

### `ai-disclosure-missing` (block)

**Fires on** a body with no line naming an AI tool alongside a preparation or
assistance verb. The match is deliberately loose so any phrasing of the
disclosure counts, not one fixed sentence.

**Fix** Add a disclosure line: '> Written by an AI agent operating for
<operator>. Verify before relying on it.'

**Grounds** The Kubernetes contributor guide is the only verified institutional
policy requiring disclosure in the description
(https://www.kubernetes.dev/docs/guide/pull-requests/). This pack's canonical
wording is the blockquote form already used elsewhere for agent-authored
content, so the disclosure reads the same way across surfaces. The older plain
sentence still satisfies the check: it matches the same loose pattern, and
retro-failing bodies written before this change would be pure audit noise with
no behavior fixed. Scoping is free here: the hook fires on an agent's Bash
tool, so every body it scores is agent-mediated by construction. The rule
needs no heuristic for whether a body was AI-written, because the trigger
already answers that. Kubernetes' companion ban on AI co-author commit
trailers is left alone; this pack's commit convention already keeps
attribution out of trailers.

### `empty-template-section` (block)

**Fires on** a heading with nothing under it, excluding a blank final section
when the body has more than one heading (a trailing blank section is almost
always optional metadata, not an abandoned one).

**Fix** Fill in the named section. Delete a heading only when it is a non-shipped
optional heading; retain every heading supplied by the repository or organization
template and fill it with applicable substance.

**Grounds** Corpus: the human-era failure mode is underfill, typically a 52-char
body that is the repo template with every section left empty. Labels confirm
it. GitHub's own docs frame templates as a delivery mechanism and make no claim
that they improve description quality
(https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates),
so an unfilled template earns nothing.

### `vacuous-opener` (block)

**Fires on** a first prose line matching a named-bad pattern: "Fix bug", "Fix
build", "Add patch", "Add convenience functions", "Moving code from A to B",
"Phase 1", "WIP", "Minor fixes", "Update", "Cleanup", "kill weird URLs". Only
lines under 200 characters are tested, so a real opening sentence is never
matched.

**Fix** Open with the behavior that changed, not a generic label like this line.

**Grounds** Google names these first lines outright as failing to provide useful
information (https://google.github.io/eng-practices/review/developer/cl-descriptions.html).
Zulip names the same failure from the other side: a summary that does not say
what part of the codebase changed
(https://zulip.readthedocs.io/en/stable/contributing/commit-discipline.html).

### `oversized-input` (block)

**Fires on** input past the scorer's robustness cap of 20,000 characters. The
body is refused outright rather than run through every regex.

**Fix** Pass the body as a file with `--body-file` instead of inline; this input
is too large to lint directly.

**Grounds** Not a judgment about length. This is the cap that keeps a pathological
input from spending the hook's timeout budget. See *Known disagreements* for why
there is no length rule underneath it.

### `em-dash` (block)

**Fires on** an em dash in prose (code fences, inline code, link targets, and
bare URLs are masked out first).

**Fix** Rewrite without an em dash; use a period or parentheses instead.

**Grounds** Corpus 26% / 0%, the cleanest discriminator measured. Already banned
by the operator's own style rules, which makes the corpus rate a confirmation
rather than the reason. Freeburg's suppression study across 12 models and 5
providers found em-dash frequency survives explicit instruction to drop markdown
and reads as a fingerprint of fine-tuning methodology
(https://arxiv.org/abs/2603.27006). That study is a single preprint about
general prose, not PR bodies, and the counter-position is on record: a single em
dash cannot convict an individual document, and em dashes are also a marker of
skilled human writers
(https://www.howtogeek.com/no-an-em-dash-cant-help-you-detect-ai-text/). The
rule survives that objection because it is a house style ban, not a detector.

### `emoji` (block)

**Fires on** an emoji codepoint in prose.

**Fix** Remove the emoji; state the fact in words.

**Grounds** Corpus 29% / 0%. No institutional source addresses emoji directly.
The plain declarative register of every source that does address tone (Google,
Zulip, the kernel) leaves no room for one, and the operator's style rules ban
emoji in technical content outright.

### `path-in-prose` (block)

**Fires on** a path-shaped token (a slash, and a short alphanumeric extension on
the last segment) in prose, outside code formatting and URLs.

**Fix** Name the behavior, not the file; the diff already lists files.

**Grounds** Corpus 24% / 2%. This is the countable proxy for the most
corroborated rule in the research pass, which no regex can test directly: the
body explains what and why, because the diff already shows how. Five independent
sources converge on it (https://google.github.io/eng-practices/review/developer/cl-descriptions.html,
https://cbea.ms/git-commit/,
https://zulip.readthedocs.io/en/stable/contributing/commit-discipline.html,
https://github.com/sourcegraph/handbook/blob/main/content/departments/engineering/dev/process/pull-requests.md,
https://docs.kernel.org/process/submitting-patches.html). A path is a "how".

### `method-narration` (block)

**Fires on** "verified with", "tested by running", "I ran", "ran the".

**Fix** State the result of verification, not how you performed it.

**Grounds** Corpus 7% / 0%. Elicited: the operator chose `Resources: 1 to
update` over a sentence describing running preview against dev and prd. Zulip
states the same rule for commit bodies, that unnecessary personal narrative
about the process does not belong
(https://zulip.readthedocs.io/en/stable/contributing/commit-discipline.html).

### `verdict-clause` (block)

**Fires on** clauses that rate the change rather than describe it: "this is a
low-risk / simple / straightforward / minor / trivial change", "no downtime is
expected", "should have no impact", "improves maintainability", "makes the code
cleaner", "straightforward", "should be safe".

**Fix** Replace the rating with the concrete fact that supports it.

**Grounds** Corpus 2% / 0%, the lowest rate of any shipped rule, so the corpus
is not what carries it. Elicited, and broadened from the elicited example to the
whole class: the operator accepted "EBS expands online, no downtime" (mechanism)
and rejected "no downtime is expected" (verdict). The distinction is that a
verdict is a claim about the change that the reader cannot check, where a
mechanism is a fact about the system that they can.

### `reviewer-instruction` (block)

**Fires on** "please review", "worth checking", "reviewers should", "take a look
at", "let me know if".

**Fix** Delete the instruction to the reviewer; let the diff and description
stand on their own.

**Grounds** Corpus 13% / 0%. Elicited: offered a targeted pointer, a generic ask,
and nothing, the operator chose nothing. This one contradicts a published
standard. See *Known disagreements*.

### `bullet-per-file` (block)

**Fires on** a list of 3 or more bullets where at least 60% lead with a filename
or path.

**Fix** Describe the behavior the files implement together, not a bullet per
file.

**Grounds** Elicited: never a bullet per file. No corpus rate was measured for
this shape specifically. The thresholds exist so a legitimately multi-part
change that names two files among six bullets does not trip it. Practitioner
sources name the anti-pattern directly (line-by-line diff restatement), but at
blog tier only; the institutional backing is the same what-and-why-not-how
convergence cited under `path-in-prose`.

### `symbol-in-prose` (warn)

**Fires on** an identifier-shaped token in prose: snake_case, camelCase, or a
bare `name()` call, outside code formatting.

**Fix** Wrap the identifier in backticks, or name the behavior instead of the
symbol.

**Grounds** Elicited, from the operator's own annotations on the labeled set:
"too many code references" is one of the recurring notes on bodies that were
passed but marked down. Warn rather than block, because the pattern also matches
legitimate prose words and product names, and a false block costs more than a
false warning. The judge picks up the density judgment this rule cannot make.

## Documented non-signals

Three candidate rules were considered against the same evidence and refused.
They are recorded here with their evidence so a future agent reading the corpus
does not re-add them.

### Markdown headers and section structure

Corpus 79% AI-era against 83% human-era. Headers are not an AI tell here because
the repos ship `.github/pull_request_template.md` supplying `## What does this
PR do?` and friends, so a rule against headers would fire hardest on the era it
is not meant to catch.

Independently corroborated. Freeburg's suppression experiment found that overt
markdown features (headers, bullets, bold) are eliminated or nearly eliminated
the moment a model is told to drop markdown, which makes them near-pure
instruction-following and close to worthless as a fingerprint
(https://arxiv.org/abs/2603.27006).

The rule is about what sits under a heading, not the heading. That is
`empty-template-section`, and it is the only structure rule that ships.

### AI-vocabulary wordlists

Corpus 1% in both eras. "comprehensive", "leverage", "robust", "seamlessly": a
rule built on that list fires on nothing and catches nothing.

The detection literature is against the approach as a class, not just against
this list. A comparison of 14 commercial AI-text detectors found none reaching
80% accuracy and only five above 70%. That figure reached the research pass at
search-summary level and was not traced to a single fetched paper, so treat it
as corroborating direction rather than a hard number. No institutional or
academic source was found endorsing wordlist detection at all. The one credible
adjacent finding (Freeburg, above) is deliberately narrow: one punctuation mark,
mechanistically explained and empirically tested, which is the opposite of a
broad vocabulary list.

### Checkboxes

Corpus 18% AI-era against 0% human-era, a clean discriminator, and still not a
defect. Operator ruling: checkboxes are legitimate whenever a template ships
them, whenever they record what testing was done, and whenever they list
post-merge steps someone has to verify.

This is the entry that shows corpus rates alone cannot decide a rule. A clean
discriminator can be a good practice the author only recently adopted. Every
shipped rule above was re-checked against that standard.

## Known disagreements

### `reviewer-instruction` runs against GitHub's own advice

GitHub's engineering blog recommends the opposite of this rule: be explicit
about the kind of feedback you want, a quick look against a design critique
(https://github.blog/developer-skills/github/how-to-write-the-perfect-pull-request/).
The corpus rate (13% / 0%) measures a real era split, but the era split is not
the argument; the elicited preference is. This rule is encoded as the operator
wants it, and the counter-citation is recorded here so the preference is not
laundered into a standard.

### A length ceiling was built, measured, and removed

The Linux kernel supplies the best argument for one: a description getting long
is a signal the patch needs splitting, which frames a ceiling as a scope
diagnostic rather than a prose-economy rule
(https://docs.kernel.org/process/submitting-patches.html). No institutional
source states a target length for a description; the kernel's is the closest
thing, and it is diagnostic, not prescriptive.

The operator's labels refuted it anyway. Passing bodies span 80 to 2242
characters and failing bodies span 0 to 1703; the ranges nest, the longest body
in the sample passed, and a 1703-character body failed. The best single length
threshold reaches 72% against a 50% baseline and earns all of it at the bottom
end, separating empty stubs from everything else. That is `empty-body`, not a
ceiling. `oversized-input` is a robustness cap on the scorer, not a judgment
about the body.

One calibration note belongs with this. Era is barred as a tuning target: the
labels put AI-era bodies at 69% pass and human-era at 33%, so a linter tuned to
flag the AI era would have been tuned toward the labels the operator rejects
more often, while reporting green.
