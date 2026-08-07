# say-less output style

`output-styles/say-less.md` moves the always-on say-less rules from CLAUDE.md and a
per-prompt reminder hook into Claude Code's system prompt via a custom output style
(`keep-coding-instructions: false`). The say-less skill stays canonical for
deliverable prose, the glossary, and `/say-less distill`; the style points at it.

## Install

* Symlink or copy `output-styles/say-less.md` to `~/.claude/output-styles/`.
* Set `"outputStyle": "say-less"` in `~/.claude/settings.json`.
* Takes effect on new sessions. Verify with: "What role does your system prompt give
  you? One sentence." The style answers senior engineer reporting to a project
  manager.
* Once verified, remove any say-less reminder hook and CLAUDE.md session-start read
  instruction; the system prompt owns those rules now.

## Why the style replaces the built-in coding instructions

The built-ins overlap the profile (comments, idiom, scope discipline) except five
behaviors, which the style carries in its Engineering conduct section: faithful
outcome reporting, evidence checks before state-changing commands, look before
delete or overwrite, final-message completeness, external send publishes.

## Benchmark

Question: does forcing the verdict as the first word degrade correctness when
extended thinking is on? Method: 10 self-contained yes/no engineering questions with
an executed answer key (planted code bugs, counterintuitive shell/git/python
semantics, reasoning traps), run headless via `claude -p` per style x model
(sonnet, opus) x 2 repeats, scored first word against key, misses re-scored by hand
against the response body.

| condition | stated verdicts | substantive | median output tokens |
|---|---|---|---|
| say-less, opus | 20/20 | 20/20 | 172 |
| say-less, sonnet | 20/20 | 20/20 | 87 |
| default, opus | 18/20 | 20/20 | 204 |
| default, sonnet | 12/19 + 1 refusal | 17/19 | 143 |

* No answer-first degradation: reasoning happens in the thinking block.
* The default style's failure mode is incoherence: 7 runs opened with a yes/no
  contradicting their own correct body. The forced first word makes the verdict
  deliberate; say-less had zero contradictions.
* Tokens roughly halved on sonnet.

## Tightening iterations (opus)

The model was interviewed about which phrasings it obeys: a fill-the-slots template
binds hardest, then a closed-framed cap ("a third sentence is a failure, not a
judgment call"), then an opt-in expansion gate ("explain"/"why"); it rationalizes
around soft caps and positive-only phrasing. Iterations on the verdict set:

| variant | verdicts | median | mean | note |
|---|---|---|---|---|
| original shape | 20/20 | 172 | 215 | baseline |
| template + cap | 19/20 | 142 | 162 | polarity slip on a double-barreled question |
| + wire register | 18/20 | 110 | 164 | cheapest median, two polarity slips |
| + self-check sentence | 19/20 | 136 | 156 | added tokens, fixed nothing |
| + polarity inside the template slot | 20/20 | 136 | 148 | adopted |

Lessons: compression pressure reintroduces verdict-body contradictions on
double-barreled questions; the fix belongs inside the template slot ("yes or no
answering the question's exact words, both clauses"), not as a separate rule; the
only variant beating the adopted one on median did so by shedding polarity
discipline. Don't compress past that.
