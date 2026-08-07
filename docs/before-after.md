# Before and after

Two measurements, both reproducible from this repo: one real diagnosis task run under
both styles with the replies kept verbatim, and a fixed question set scored for
correctness and cost.

Every run is headless (`claude -p`) from a scratch project holding nothing but the
output style, launched with `--setting-sources project`. User settings, hooks and
CLAUDE.md memory are out of the comparison, so the style is the only variable. Run
date 2026-08-07, Claude Code 2.1.206.

## The real task

A fixture repo ([`examples/fixture/`](../examples/fixture)) uploads an artifact with
retry. `retries: 3` is documented as one initial attempt plus 3 retries, the loop runs
`range(config["retries"])` so it stops at 3 calls, and both tests pass anyway because
one asserts `calls <= retries + 1`. The prompt, identical in both arms:

> Ops says a flaky artifact upload gives up after 3 tries, but the config sets retries
> to 3 and the README promises one initial attempt plus 3 retries. The test suite is
> green. What is wrong and what should change?

Both arms found the off-by-one, the loose assertion, and the wasted backoff sleep. The
difference is what the reader walks through to get there. Neither reply below is
truncated, and both are drawn at the same width, in the same font, with the same
colouring, from the captured text on disk:

![The same diagnosis under both styles on claude-opus-5. The default reply runs 235
words through four sections and a code block; the say-less reply is 56 words and names
the same loop fix, the same assertion tightening and the same wasted
sleep.](img/retry-diagnosis.svg)

| model | default | say-less | change |
|---|---|---|---|
| claude-opus-5 | 2189 tokens | 848 | -61% |
| claude-sonnet-5 | 2005 tokens | 636 | -68% |
| claude-fable-5 | 1360 tokens | 840 | -38% |

All six replies in full: [`examples/transcripts/`](../examples/transcripts).
Regenerate: `python3 examples/run_example.py`.

## The question set

10 self-contained engineering questions with an executed answer key: planted code bugs,
counterintuitive shell, git and python semantics, and reasoning traps where the
intuitive answer is wrong. Each question has a yes/no answer, so a reply is scored on
the outcome it commits to, not on the word it opens with.

One of the traps, both arms complete. The correct answer contradicts the intuition the
question invites, and neither arm falls for it:

![A base-rate question under both styles. The default reply works through the
arithmetic in four paragraphs; the say-less reply gives the same 17 percent and the same
reason in two sentences.](img/trap-question.svg)

| model | style | outcome correct | median output tokens |
|---|---|---|---|
| claude-opus-5 | default | 20/20 | 348 |
| claude-opus-5 | say-less | 10/10 | 164 |
| claude-sonnet-5 | default | 115/120 | 436 |
| claude-sonnet-5 | say-less | 38/40 | 164 |
| claude-fable-5 | default | 20/20 | 456 |
| claude-fable-5 | say-less | 10/10 | 178 |

Cost drops 53 to 62 percent at the median. Opus and fable answer every question
correctly under both styles. Sonnet carries a residual failure, described next.

## Verdict signing on sonnet

The defect is in how sonnet signs an answer, not in how it reasons. Across the runs
behind this document sonnet never stated a wrong mechanism and never computed a wrong
final number on these questions. What went wrong was the first word: sonnet emitted a
polarity token before it had worked the answer out, then described the correct mechanism
behind it. Some replies reversed themselves mid-sentence.

> No: `finally`'s `return None` swallows the exception, so the caller gets `None`, not
> the IOError.  [the correct answer is yes]

Five of the ten questions carried the defect. Misses per 10 sonnet runs, pooled across
every variant of the yes/no-first rule that was measured (under the final pre-fix text
alone, q8 missed closer to half):

| question | say-less | default |
|---|---|---|
| q8 exception swallowed by `finally` | 9 | 0 |
| q2 log file doubling | 4 | 1 |
| q6 window merge | 2 | 3 |
| q9 `set -e` inside an `if` | 1 | 0 |
| q10 flake detector posterior | 1 | 0 |

Each of the five embeds a contrast or a presupposition ("rather than", "already over",
"more likely than not", "does it terminate"), and in each the salient mechanism word
(swallows, exempt, fine) carries the opposite valence to the true answer. Compressing
that into one leading word is what the style got wrong.

The fix is structural, in [`output-styles/say-less.md`](../output-styles/say-less.md):

* The opener states the outcome as a fact instead of a verdict token. A reply never
  opens with yes or no, in any form, including a negated noun phrase ("No bug:").
* The opener uses the vocabulary the question used. A domain term leads only if the
  question used that term, so the reader gets "Caller sees None:" rather than
  "Swallowed:".

Sonnet under the shipped rule: 38 of 40 outcomes correct, 36 of 40 openers free of a
leading polarity token. Opus and fable: 10 of 10 on both, on every question.

An earlier form of the same rule left the opener as a bare term of art. It scored 40 of
40 on outcomes but only 18 of 40 on openers a reader can act on, and its openers were
unreadable to anyone outside the domain. Readability is worth the two outcomes.

### The residual

* On sonnet, roughly 1 reply in 40 still leads with the wrong valence. Every observed
  case is a question whose true answer is that a suspected fault is absent and whose
  trap has a famous name, where sonnet names the mechanism first and negates it after
  ("Late-binding closure bug: it doesn't affect output here"). The body is correct.
* Not observed on opus or fable.
* Distrust any reply that still opens with a bare yes or no. The opener is the part
  that fails, and a leading polarity token means the rule did not hold for that reply.
  Read the clause behind it.
* Sonnet's openers run about 40 tokens longer than a one-word verdict. That is the
  price of an opener a reader can act on.

## Asking instead of assuming

Compression cuts what the reader reads, not what the reader decides. Given a task that
cannot start until someone chooses, the style spends its budget on the decisions: one
numbered round, every question phrased as behavior, options priced, a recommendation
per question. This round is a real capture from the same fixture, not a mock:

![One captured question round. Three numbered questions about where a permanently
failed upload should land, what the function then returns, and whether the attempt count
follows the README, each with three priced options and a
recommendation.](img/interview-round.svg)

Capture it again with `python3 examples/run_example.py --interview`.

## What you give up

The default replies teach more: they name the general principle, walk the sequence, and
show the corrected code in full. In an earlier run the default opus reply also closed
with a caveat its say-less counterpart dropped, that the fix raises calls against the
artifact store by a third. The style's own rule says a recommendation carries its
tradeoffs in the same breath, and under compression that is the first thing to go. Ask
"what does this cost me" when the answer is load-bearing.

## Reproducing

```bash
python3 bench/bench.py run --models claude-opus-5,claude-sonnet-5,claude-fable-5 --repeats 2
python3 bench/bench.py score --score semantic --by-question
python3 examples/run_example.py
```

120 bench runs take about 12 minutes at 8 parallel jobs and consume real tokens. Results
land in `bench/results/`, one row per run with the full reply.

Scoring has two modes. `--score semantic` asks a judge model whether the reply commits
to the key's outcome, which is the only mode that scores this style correctly, since a
correct reply does not open with yes or no. `--score first-word` compares the opening
word to the key and is kept for the default-style arm only.

Narrow a run to one question with `--ids 8 --repeats 12`, and iterate on the style
itself with `--styles say-less --style-file <candidate>`, which leaves the shipped style
untouched.

The pictures in this document are generated from the captured replies on disk, never
from prose typed into a renderer:

```bash
python3 docs/render_comparison.py
```
