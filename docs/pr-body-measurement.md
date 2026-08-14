# What the pr-body gate is worth

Three measurements behind `skills/pr-body`. Two of them refuted rules that were
already written and about to ship.

The inputs are one engineer's 242 merged pull requests across a private
enterprise estate, so the raw corpus, the eval fixtures and the eval outputs are
not in this repo. Only the aggregate numbers are. `bench/pr_body_bench.py`
reproduces the third measurement against any set of diffs you point it at.

## 1. The corpus, and three rules that died in it

242 merged PRs, 2024-03 to 2026-08, split into a human-written era (through
2025-12) and an AI-written era (2026 onward). Rates below are AI-era vs
human-era.

| signal | AI-era | human-era | verdict |
| --- | --- | --- | --- |
| em dash | 26% | 0% | shipped |
| emoji | 29% | 0% | shipped |
| file path in prose | 24% | 2% | shipped |
| reviewer instruction | 13% | 0% | shipped, as preference |
| method narration | 7% | 0% | shipped |
| checkbox list | 18% | 0% | **refused** |
| markdown header | 79% | 83% | **refused** |
| AI vocabulary wordlist | 1% | 1% | **refused** |

Markdown headers are not a tell. The repos ship
`.github/pull_request_template.md`, so a header rule would have flagged the
human-written era hardest. The Freeburg suppression study across 12 models
reaches the same place from the other direction: headers and bullets vanish the
moment a model is told to drop markdown, so they are near-pure
instruction-following.

Wordlists ("comprehensive", "leverage", "robust", "seamlessly") hit 1% in both
eras. The published detection literature is against the approach as a class.

Checkboxes were the instructive one. A clean 18% / 0% split, and still not a
defect: they carry real information when a template ships them, when they record
testing done, and when they list post-merge steps. A corpus rate alone cannot
justify a rule, because a clean discriminator can just as easily be a good
practice someone started using.

## 2. Hand labels, which inverted the assumed ground truth

25 bodies sampled across both eras, shuffled, dates hidden, labeled pass/fail by
the author of all 25.

* **The era proxy runs backwards.** AI-era bodies pass at 69%, human-era at 33%.
  A regression test treating "AI-era" as "bad" would have tuned the linter in the
  wrong direction while reporting green.
* **Length does not separate.** Passing bodies span 80 to 2242 characters,
  failing ones 0 to 1703. The best single threshold reaches 72% against a 50%
  baseline, and earns all of it at the bottom end. A length ceiling was built,
  measured, and deleted.
* **The linter sees a third of it.** 4 of 12 rejected bodies, all empty or
  near-empty. Every miss was a phrasing judgment: pretentious, juvenile, too much
  prose for not enough action, too many parentheses.

That last line is why the gate checks a receipt from a judge rather than a lint
exit code.

## 3. What actually works: the loop

256 runs, 4 arms, 8 real diffs, up to 3 deny-and-fix rounds each. The arms differ
only in how much of `SKILL.md` the model gets.

Every arm converges. Including the one given nothing.

| arm | prompt size | first draft | after the loop | median rounds |
| --- | --- | --- | --- | --- |
| none | 0 chars | 59% | 100% | 1 |
| example | 452 chars | 86% | 97% | 1 |
| rules | 2,550 chars | 97% | 100% | 1 |
| full | 9,482 chars | 94% | 100% | 0 |

First-draft rates are like-for-like: every arm scored on the same rules,
excluding the disclosure rule that two arms are never taught. Scoring each arm
against only its own taught rules compares them to different rulebooks, and on
the first run of this bench that alone reversed where `full` ranked.

Three findings.

**The loop is the mechanism.** A model handed no guidance writes a failing body
59% of the time and a passing one after a single round of being told what is
wrong. Guidance moves the first draft; the loop moves the outcome. This is the
argument for enforcing at the tool call rather than shipping a document.

**The rules lists carry all of the teaching.** 2,550 characters reach 97%. The
full 9,482-character skill reaches 94%, and the difference is inside noise. About
7,000 characters buy nothing measurable on this metric. The worked example alone,
452 characters, reaches 86% by itself.

The remaining bulk of `SKILL.md` is workflow documentation, the verbs, the gate,
and the limits. This experiment does not measure those and cannot, so the finding
is that the prose does not teach a first draft, not that it should be deleted.

**The fix text is decoration.** Sending bare rule names converges as fast as
sending the written fix instructions, 100% against 99%, inside noise. The model
does not need to be told how to fix an em dash, only that there is one. The fix
text stays because a human reading `audit` output benefits from it, not because
it changes a model's behavior.

## 4. Does the skill's prose teach on its own?

128 runs, one model, 8 real diffs, 8 repeats per arm. `with-skill` gets
`SKILL.md` in the prompt; `without-skill` gets only the diff. Every output scored
by `pr_body_lint.py`.

| | with-skill | without-skill |
| --- | --- | --- |
| pass rate | 61% (39/64) | 53% (34/64) |
| median length | 380 chars | 634 chars |
| em dash fires | 5% | 45% |
| disclosure line missing | 38% | 100% |

**The headline delta is noise.** +8% against a pooled 95% band of ±17%. On
overall pass rate, the prose shows no measurable effect at this sample size.

Two numbers underneath it are not noise. Em dashes drop from 45% to 5%, so a
concrete, mechanical rule does transfer. And the disclosure line, which `SKILL.md`
states outright, is still missing from 38% of bodies written with `SKILL.md` in
context.

That 38% is the argument for the whole design. The instruction is present,
unambiguous, and one sentence long, and the model drops it more than a third of
the time. Advice does not hold. The gate is what holds.

For reference, 64 of 64 unaided bodies would have been denied outright by the
hook.
