# Writing for agents

Adapted from Matt Pocock's writing-for-agents (github.com/mattpocock/skills), fetched 2026-08-06.

Everything an agent reads before or during a task — a skill, a `CLAUDE.md`/`AGENTS.md`
line, a disclosed reference file — is one document type with one job: make the agent
take the same *process* on every run, not the same output. The rest of this file is the
vocabulary for judging whether a document does that job.

## Pointers

A **pointer** is anything in the agent's always-loaded context that names material
living outside it and states the condition for reaching it: a skill description, a
`CLAUDE.md` line naming a doc, a "see references/x.md" sentence. The pointer's wording
decides whether the agent reaches the material, not the material's quality — a critical
doc behind a vague pointer is a bug in the pointer, not the doc. Sharpen the wording
before inlining the material; inlining is the expensive fallback.

A pointer has two jobs: say what the target is, and list the branches (distinct cases)
that should send the agent there. Rules for writing one, in order of how much they cost
to skip:

* **Front-load the trigger word.** The word that should fire the pointer belongs at the
  front, where it does its matching work, not buried mid-sentence.
* **One trigger per branch.** Three synonyms for the same case are one branch written
  three times — collapse them. Keep only branches that actually diverge.
* **Cut identity the body already carries.** Don't restate in the pointer what the
  target document says about itself in its own first line.

## Two kinds of load

Every document and pointer spends one of two budgets:

* **Context load** — cost on the agent's window. Anything always loaded (a skill
  description, a `CLAUDE.md` line) pays this on every single turn, whether or not it
  fires that turn.
* **Cognitive load** — cost on the human, who has to remember the document exists and
  when to reach for it. Not a cost to eliminate; it's the price of leaving a judgment
  call to a person. Spend it where the human's judgment matters, cut it everywhere else.

Content behind a pointer trades context load for the pointer's own (small) footprint.
Content with no pointer at all rides entirely on the human remembering it.

## Information hierarchy

Rank every piece of content by how urgently the agent needs it:

1. **In-file step** — the ordered actions, inline. What runs first.
2. **In-file reference** — rules, definitions, a flat list consulted as needed. Still
   loaded every time, but not part of the sequence.
3. **Disclosed reference** — pushed to a separate file, reached only through a pointer
   that fires on demand. Ranges from a sibling file in the skill's own folder to a
   fully external doc any skill can point at.

**Progressive disclosure** is moving content down this ladder so the top stays scannable.
Use the **branching test** to decide what moves: if every branch needs it, keep it
in-file; if only some branches reach it, push it behind a pointer. Reference that should
have been disclosed but sits in-file buries the steps around it — the agent's attention
on "what do I do next" competes with "here's a fact you may not need."

**Co-location** is the in-file version of the same instinct: keep a concept's definition,
rules, and caveats under one heading instead of scattered across the document. A reader
(or agent) hitting one part should get its neighbors for free. This is different from
duplication — duplication repeats one meaning in two places; scattering spreads one
meaning across many, with none of them complete.

**Sprawl** is what happens when nothing gets disclosed and nothing gets pruned: the
document is long *and* every line is technically relevant, so there's nothing to cut, but
attention still thins across the length. The fix is always structural — disclose, or
split — never "trim adjectives."

## Completion criteria

Every step needs a condition that tells the agent "this is done." Two properties matter:

* **Clarity** — can done be told from not-done at a glance? A fuzzy bound ("understand
  the codebase") invites **premature completion**, where the agent's attention slides
  toward the *next* visible step before this one is actually finished. Fix the wording
  first — sharpen the bound. Only split the sequence (hiding later steps behind a real
  context boundary — a hand-off, a subagent call, not an inline function call) if the
  bound is genuinely irreducible and you've actually observed the rushing.
* **Demand** — how much work the criterion requires. "List every file touched" is
  weaker than "confirm every touched file compiles." High-demand criteria drive legwork
  — digging the agent does without being told to dig, because the bar forces it. This
  applies to flat reference too: "every rule checked" is a demand bar on a rule list,
  not just on a step sequence.

## Splitting a document

Splitting spends load, so only split when it earns it back:

* **By sequence** — cut a long run of steps where later steps visible in the same file
  tempt the agent to rush the current one. Splitting hides them behind a real boundary
  and forces full attention on the step at hand. Don't do the reverse: merging two
  sequences that were split for this reason reopens the premature-completion risk.
* **By invocation** — skill-specific; the trigger is a genuinely separate leading word
  the agent (or another skill) should be able to fire on its own. See the Doctor
  section of this skill's SKILL.md for how this plays out with model- vs user-invoked
  skills.

## Leading words

A **leading word** is an existing, pretrained concept (*tracer bullet*, *fog of war*,
*tight loop*) that the model already has priors for. Using it as a token — never
re-explained as a full sentence each time — recruits those priors for free; coining a
new term instead means paying definition tokens the pretrained word would have given
you at no cost.

A leading word does two things: in the body, it anchors *execution* — the agent reaches
for the same behavior every time the word shows up. In a pointer, it anchors
*invocation* — when the same word appears in your prompts, your docs, and the codebase
itself, the agent connects them and reaches the pointer more reliably.

Hunt for restatements to collapse: if a document keeps re-describing the same triad or
gesture in different words each time, that's a leading word waiting to be minted or
borrowed. "Fast, deterministic, low-overhead" collapses to *tight*. A vague "a loop you
trust" collapses to a binary *red/not-red* state.

**Negation is the trap next to this lever.** Telling the agent what *not* to do puts the
forbidden behavior directly in context and makes it more available, not less — "don't
use em-dashes" activates em-dashes. State the positive target instead ("use short
sentences and parens for asides") so the banned behavior never gets named. Keep a bare
prohibition only as a hard guardrail with no honest positive phrasing, and even then
pair it with the positive target so the agent has somewhere to put its attention.

## Pruning

* **Single source of truth.** Each meaning lives in exactly one place. Duplication —
  the same meaning stated twice — costs upkeep (two places to update) and inflates that
  meaning's apparent importance beyond what it deserves. Not the same as a leading word,
  which repeats a *token* on purpose while the meaning stays singular.
* **Cache vs. environment.** The environment — `package.json`, config files, `--help`
  output, the directory layout — is already a source of truth. A document that restates
  it is a cache, and a cache only earns its keep when the lookup it replaces is
  expensive. Document the unwritten convention or the gotcha the environment can't
  confess; skip the one-command lookup the agent can just run.
* **Relevance and sediment.** Ask of every line: does it still bear on what this
  document does? A line stops being relevant when it never mattered (padding, or a
  branch that should have been disclosed) or when the world it describes moved on.
  Without active pruning, stale material accumulates as **sediment** — nobody wants to
  be the one to delete a line that might still matter, so it never gets deleted, and the
  document thickens with dead weight.
* **No-ops.** A no-op is an instruction the model would already follow by default —
  stating it spends tokens to change nothing. Test it against actual behavior, not
  intuition: run the document and see if removing the line changes anything. If it's a
  no-op, delete the whole sentence, not just a few words from it. This test also catches
  weak leading words: "be thorough" against a model that's already thorough-ish is a
  no-op; the fix is a stronger word ("relentless"), not a longer sentence.
