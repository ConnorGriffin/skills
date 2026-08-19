# The voice judge

The linter already ran. It checked countable defects and found none, which on
the operator's labeled set means very little: it caught 4 of 12 rejected bodies
and all 4 were empty or near-empty. Everything that decided the other 8 was
phrasing. That is what this pass is for.

The judge reads voice. It does not re-check rules, re-count characters, or
verify that the change is correct.

It reads the body **and the diff**. The diff is not there to be reviewed. It is
there for one question the body cannot answer on its own: does the change do
something the body never mentions? That is the eighth texture below, and it is
the only one the diff is used for.

## Output

A verdict and line-level rewrites. Never a score on its own, and never a note
that the body "could be tightened" without saying which line and to what.

```json
{
  "verdict": "rewrite",
  "rewrites": [
    {
      "line": 1,
      "was": "This PR undertakes a comprehensive overhaul of the volume sizing story.",
      "now": "Grows the appliance data volume from 2 TB to 4 TB."
    },
    {
      "line": 3,
      "was": "",
      "now": "* Capacity alarm threshold follows the new size, 1600 to 3200 GiB."
    }
  ]
}
```

An entry with an empty `was` is an added line, and `line` is the line it follows
(0 for the top of the body). Every other entry replaces the line it names.

`pass` carries an empty `rewrites` list. A `rewrite` verdict with no rewrites is
malformed output, not a soft fail.

## Bias toward passing

Pass unless a specific line is wrong and you can write the line that replaces
it. If the honest reaction is "this reads a bit long", that is a pass.

The tradeoff is deliberate and it is asymmetric. A false deny costs the operator
a rewrite cycle on a body that was already fine, on a change that is otherwise
ready to merge. A false pass costs one mediocre PR description. The second is
cheaper, so the judge takes that side of the error.

Two consequences worth stating outright. One genuine parenthesis is not a
finding, and one long-ish paragraph is not a finding. A finding needs a pattern
the reader would notice, or a single sentence that is plainly wrong.

## What to look for

Eight textures, each drawn from the operator's own annotations on real bodies.
Examples first; the rules underneath them are short on purpose, because the quiz
that produced these preferences showed examples carry voice where abstract rules
do not.

### Invented motivation

The author is claiming to know something they do not. The most reliable single
finding in the set, and the one worth being least lenient about.

> Grows the data volume ahead of the next release cycle, so capacity is in place
> before traffic picks up.

Becomes:

> Grows the data volume from 2 TB to 4 TB. It has been running near capacity.

If the ticket said why, that reason is a fact and belongs. If nobody said, the
body says what changed and stops. Tells: "in preparation for", "ahead of", "so
that the team can", "as part of our ongoing".

### Verdict clauses that rate rather than describe

The linter catches the stock phrasings. The class is wider than the list, and
new phrasings are exactly what the judge is for.

> The blast radius here is quite contained and reviewers can be confident this
> lands cleanly.

Becomes:

> One resource updates. EBS expands online.

Test: could the reader check this sentence against the system? A mechanism can
be checked. A rating cannot.

### Parenthetical density

> Grows the volume (currently 2 TB, provisioned in 2023) to 4 TB (the next size
> that clears the projected growth curve), with no change to the snapshot
> schedule (which already runs nightly).

Becomes:

> Grows the volume from 2 TB to 4 TB. The nightly snapshot schedule is
> unchanged.

One parenthesis in a body is fine. Three in a sentence is an author negotiating
with themselves in public.

### Inline-code and symbol density

> Updates `volumeSize` in `NewApplianceStack()` so `pulumi up` produces the
> larger `aws.ebs.Volume`.

Becomes:

> Grows the appliance data volume to 4 TB.

Every backticked symbol sends the reader to the diff to find out what the
sentence meant. Name the behavior instead. A symbol earns its place when the
symbol itself is the fact the reader needs (a config key they will set, a flag
they will pass).

### Paragraphs where bullets belong

> This change updates the volume size, and it also raises the alarm threshold so
> the new capacity is reflected, and the runbook has been updated to match, plus
> the dashboard query needed a small change to pick up the new dimension.

Becomes:

> * Volume grows from 2 TB to 4 TB.
> * Capacity alarm threshold follows the new size.
> * Runbook and dashboard query updated to match.

A list of facts is a list. Prose is for the one place it earns its keep, which
is the risk mechanism.

### Prose volume with no action behind it

The most common annotation on the labeled set: "too much prose for not enough
action". Weigh the word count against the number of distinct facts, not against
the diff.

> This pull request represents an incremental step in our capacity management
> approach for the appliance fleet. Storage pressure has been an ongoing area of
> attention, and this change addresses it directly by adjusting the provisioned
> capacity of the data volume upward, bringing it into line with observed usage
> patterns and giving headroom for the foreseeable future.

Becomes:

> Grows the appliance data volume from 2 TB to 4 TB. It has been running near
> capacity.

Three sentences carrying one fact is a rewrite. So is a five-bullet list where
two bullets restate the other three.

### Pretentious or juvenile phrasing

Both directions of the same failure, and both appear in the labels.

Pretentious:

> This change harmonizes the storage posture of the appliance tier with the
> realities of its consumption profile.

Juvenile:

> Turns out the disk was basically full! Bumped it up so we should be good now.

Both become:

> Grows the appliance data volume from 2 TB to 4 TB. It has been running near
> capacity.

### A load-bearing fact the body omits

The only texture that needs the diff, and the only one that catches underfill.
The labeled set rejects short bodies as well as long ones (a 77-char body
annotated "way too thin", among others), and no length threshold separates them:
an 80-char body passed and an 82-char one failed. The defect is never the size.
It is that the change did a second thing and the body mentions only the first.

Body:

> Grows the appliance data volume from 2 TB to 4 TB. It has been running near
> capacity.

Diff: the volume grows, **and** the capacity alarm threshold moves from 1600 to
3200 GiB.

Add:

> * Capacity alarm threshold follows the new size, 1600 to 3200 GiB.

Fires on exactly two shapes:

* The change does something a reader of the body would not expect from the body.
* A second distinct thing changed, and only the first is mentioned.

Hard boundary, because this is the one rule that could turn the judge into a
code reviewer. It does not fire on style, correctness, scope, test coverage, or
whether the change is a good idea. Those stay on the list below, diff or no diff.

The rewrite is always the missing fact, written out as the line to add. Never
"add more detail", never "expand on the rationale". If you cannot state the
missing fact in one line, there is no finding.

The fact has to be load-bearing, not merely present in the diff. A renamed local
variable is in the diff and belongs nowhere near the body. The test is whether a
reviewer who read only the body would be surprised by what they find.

## Not the judge's business

Do not raise any of these. The rest of the system owns them, and a judge that
wanders into them produces findings the author cannot act on.

* Length, in either direction. There is no target and no ceiling, and the judge
  never asks for more words. It asks for one named missing fact, or for nothing.
  A body of one true line that omits nothing is a pass.
* Markdown headers, and any section the repo's PR template supplies.
* Checkboxes. Legitimate when the template ships them, when they record testing
  done, and when they list post-merge steps to verify.
* The AI disclosure line. Boilerplate, not authored prose.
* Anything the linter already reported. It ran first.
* Whether the change itself is correct, well-scoped, or a good idea. Having the
  diff does not change this. The diff answers one question only: did the change
  do something the body never mentions.

## The prompt

Paste the body under this with line numbers, then the diff.

> You are judging the voice of a pull-request body. A deterministic linter has
> already checked it for countable defects and found none, so do not look for
> file paths, em dashes, emoji, or stock verdict phrasings. Judge only how it
> reads, plus one question about coverage (rule 8).
>
> You are given the body with line numbers, and the diff of the change. The diff
> is not for review. Use it only for rule 8.
>
> Return JSON: a `verdict` of `pass` or `rewrite`, and a `rewrites` list, each
> entry carrying `line`, `was`, and `now`. `now` is the replacement text,
> written out in full. An entry with an empty `was` is a line to add after
> `line` (0 for the top). Never return a rewrite you cannot write the
> replacement for, and never return a score or a general comment in place of a
> rewrite.
>
> Be biased toward passing. A false deny costs a rewrite cycle on a body that
> was fine, which is worse than letting one mediocre body through. One
> parenthesis is not a finding. One long paragraph is not a finding. Pass unless
> a specific line is wrong, or a specific fact is missing.
>
> Raise a rewrite for any of these, and nothing else:
>
> 1. Motivation the author could not know. "Ahead of the next release cycle"
>    when nobody said that.
> 2. A clause that rates the change instead of describing it. The reader can
>    check a mechanism, not a rating.
> 3. Parenthetical asides stacked up, several in a sentence or throughout.
> 4. Inline code spans and symbol names where the behavior would say it better.
> 5. A paragraph carrying a list of facts that should be bullets.
> 6. Word count out of proportion to the number of distinct facts.
> 7. Phrasing that reads as pretentious, or as juvenile.
> 8. A fact the diff makes load-bearing that the body does not mention: the
>    change does something a reader of the body would not expect, or a second
>    distinct thing changed and only the first is named. The rewrite is the
>    missing fact written out as a line to add, never a request for more detail.
>    If you cannot state it in one line, there is no finding. A fact that is
>    merely present in the diff (a renamed local, a reformatted block) is not
>    load-bearing.
>
> Say nothing about length, markdown headers, template sections, checkboxes, the
> AI disclosure line, or whether the change is correct, well-scoped, or a good
> idea. Never ask for more words. Ask for one named missing fact, or for nothing.
