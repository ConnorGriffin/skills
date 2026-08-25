---
name: persona-review
description: Convene a small panel of persistent reviewer personas (curated colleague-likenesses plus invent-on-demand) to review a document cold, in character, then synthesize a panel verdict. Use when the user wants a document reviewed by a panel, wants named perspectives on a plan or design, or when another skill (e.g. plan-review) convenes a persona panel for a load-bearing review.
---

# Persona review

A panel of reviewer personas reads a document cold, each from its own memory, and
returns a position in its own voice. The skill picks the panel, runs each reviewer
in isolation, and synthesizes the verdict. Personas persist across reviews: what a
panelist decided last time is not re-litigated unless the document changed the
grounds for it.

## Verbs

- **`review <doc>`** (default). Pick a panel, review cold, synthesize a verdict.
- **`mine <person> <org|org/repo>`**. Build or refresh a real-colleague persona's
  profile from their actual PR history within the given scope. Also the re-mine
  command.
- **`roster`**. List available personas: curated, real-colleague, and invented-and-kept,
  each with its last-mine date (real-colleague) or last-used date, derived from its
  newest review-log entry.

## First-time setup

This skill ships no personas and no personal data. Persona memory lives in a
separate **data repository** you own, resolved by a config pointer:

1. `PERSONA_REVIEW_HOME` env var (the data repo path itself), if set, else
2. `$XDG_CONFIG_HOME/persona-review/config.json` (or `~/.config/persona-review/config.json`),
   containing `{"data_repo": "<path>"}`.

If `PERSONA_REVIEW_HOME` already resolves to a data repo, skip straight to the
`CONTEXT.md` check below. Otherwise, if neither pointer resolves, or the resolved
data repo has no `CONTEXT.md`, walk the user through:

1. Creating a private repo (not this one) to hold persona memory.
2. Proposing the config pointer file's contents (path and format above) and writing
   it only after the user approves it. Skip this step when `PERSONA_REVIEW_HOME`
   already resolves.
3. Proposing a starter `CONTEXT.md` for that repo (the data repo's own schema
   document, distinct from any project domain glossary), covering:
   - **Record types:** persona profile, review-log entry, override ruling.
   - **Supersession rule:** a stance change is a new record linking the record it
     supersedes; existing records are never edited in place.
   - **Distillation rule:** records hold distilled stances and quoted evidence lines,
     never full transcripts of a review or a mined PR.
   - **Grounds rule:** every condition in a review-log entry, blocking or note,
     ends with a labeled clause `grounds: when <document-independent property>`
     alongside the document-specific detail. Grounds are what a future review
     tests to decide whether a new document reopens the point.
   - **Disposition rule:** a later review that finds a prior condition met or
     mooted records that disposition in its own entry, never by editing the
     old one.

   Show the proposed `CONTEXT.md` and commit it to the data repo only after the user
   approves it. Never write persona memory, profiles, or mined evidence into this
   skill's own repository.

Every later write to the data repo follows the data repo's own `CONTEXT.md` for record
shape and layout — read it before writing, and defer to it over the shapes described
here if the two disagree. That deference is scoped to shape and layout only: approval
before commit, append-only logs, supersession-not-mutation, and distilled-not-transcript
records hold regardless of what the data repo's `CONTEXT.md` says.

This data repo is this skill's only persona store, separate from `ui-craft`'s
project-local `.claude/qa/personas`: design-surface persona critique belongs to
`ui-craft`, not here.

## Roster

Two kinds of persona:

- **Curated.** Named archetypes (e.g. "the security skeptic", "the API minimalist")
  with a profile grown by its review log like any other persona. There is no
  dedicated creation verb: a curated persona enters the roster by the user keeping
  an invented persona after a review (below), or by the user describing one
  directly to add to the roster, proposed as a record under the same approval
  gate as any other write.
- **Real-colleague.** Carries the person's real name, and every attribution of its
  output (its own position, the synthesized verdict, and any hand-back to a
  calling skill) is labeled as a simulation of that person with its mine date,
  never presented as their actual words. Its profile is built by `mine <person>`,
  not invented. That labeling governs chat and hand-back attribution only;
  for anything committed to a project repository, containment below wins and the
  name does not appear at all.

**Invent-on-demand.** When no roster persona fits a document's concerns, invent one
for this review (state its stance and evidence-gathering approach up front). It
persists to the roster only if the user says to keep it after the review; otherwise
discard it at review close, and its review-log entry from this review is dropped
along with it rather than written to the data repo.

## Containment: names never leave the session

Persona names, the simulation label, mine dates, and any panel narrative exist in
exactly two places: the chat conversation, and the private persona data repo.

No file written to a project repository may carry any of it. That covers design
docs, ADRs, plan documents, PR bodies, commit messages, review artifacts, ledgers,
and anything else committed anywhere other than the persona data repo. No persona
name (real or invented, curated or colleague), and no "reviewed by", "panel", or
"simulated" framing.

When panel findings belong in a committed artifact, they go in as plain content:
conditions, decisions, open questions. Not anonymized attribution ("a security
reviewer noted..."). No attribution at all.

This binds calling skills too. A verdict handed back to another skill carries
attribution because it is written for the chat; the caller strips every trace of
it before anything reaches a repo.

## Mining a real colleague

`mine <person>` builds or refreshes a profile from that person's actual pull request
history using the GitHub CLI (`gh`). The user must supply the repo or org to search
(`mine <person> <org/repo>` or `<org>`) — never crawl unbounded across the estate.
Within that scope, pull: review comments they left, their approval patterns (what
they wave through vs. what they block on), and concerns that recur across reviews.
Distill to stances and short evidence quotes; do not store full comment transcripts.
Write the profile as a new, dated record (a refresh supersedes the prior profile
record rather than editing it) and show the proposed record for approval before it
commits.

At `review` time, check every real-colleague panelist's last mine date. Flag any
older than one quarter and suggest a re-mine before or after the review; an unmined
or stale profile does not block the review, it is just weaker evidence for that
panelist's positions.

## Panel composition

For `review <doc>`, pick 2-3 personas whose known concerns match what the document is
actually about (a data-model change draws a different panel than a UI change). Before
review starts, state the panel and, for each pick, the one-line reason it was chosen.
Prefer roster personas; invent only when no roster persona's concerns cover a topic
the document raises.

## Panelist dispatch

The coordinator supplies the selected adapter, explicit reviewer model, and explicit
reviewer effort. For each panelist, dispatch only through
`skills/drivers/orchestrate/scripts/codex-worker.py` or
`skills/drivers/orchestrate/scripts/claude-worker.py`, using the selected adapter's
read-only review surface. Never use the built-in Agent tool, Workflow tool, or
background-agent machinery.

Each dispatch has one coordinator-owned state file under the coordinator's
session-scratch directory. Use the adapter's start, resume, stop, and verify surface;
adapter state, same-worker resume, and recovery remain adapter-owned.

The coordinator keeps the non-sensitive positional prompt text in session scratch and
passes that text to the selected adapter. The prompt tells the panelist to read the
document, its private persona profile, relevant review-log entries, and relevant
override rulings from their existing locations; review cold without access to another
panelist's output or the synthesis; and return positions, blocking or note conditions,
and approval or refusal. The prompt contains no persona name, simulation label, mine
date, panel narrative, or profile, review-log, or override content.

## Cold review, per persona

Each panelist reviews independently and cold: no visibility into the document under
any other panelist's read, and no access to the panel's eventual synthesis while
forming its own position. Follow [Panelist dispatch](#panelist-dispatch) for each
panelist, handing it only:

- The document under review.
- That persona's profile (stances, style, evidence quotes) — the panelist's only
  stance source.
- That persona's review-log entries relevant to this document's topic, to test
  against this document (is a settled point reopened, is a prior condition met
  or mooted). A panelist does not mine log entries for new opinions.
- Override rulings relevant to this document's topic (settled points a prior review
  already closed — do not re-raise them unless the document reopens the grounds for
  them).

Where adapter dispatch isn't available, review personas serially in the main session,
deliberately not looking back at an earlier persona's output while forming the next one's position.

Each panelist's output: positions taken, conditions imposed (each marked **blocking**
or **note**), and an approval or refusal — all in the persona's voice, grounded in its
profile's evidence quotes. A persona whose profile has no bearing on some part of the
document says nothing about that part rather than inventing an opinion.

## Synthesis

Combine the panelists' outputs into one verdict:

- **Unanimous** or **split**, stated plainly.
- Every **blocking** condition from any panelist, attributed to that panelist.
- **Note**-level conditions listed separately; they inform but don't block.

## Close: memory writes

At review close, batch every proposed memory write into one approval pass:

- A review-log entry per panelist (position, conditions, approval/refusal) — append,
  never edit a prior entry.
- A distill line per blocking condition each panelist imposed: the
  document-independent stance it instantiates ("blocks when <property of a
  document>"). A stance absent from or changed against that panelist's current
  profile goes into a superseding profile record in the same batch — profile
  growth is a required close output, not an incidental one.
- Any override ruling the user makes during close (accepting a document over a
  panelist's blocking objection, or dismissing a note) — recorded so the same point
  isn't re-raised next time this document's topic comes up.
- Whether any invented persona is kept on the roster.

Show the full batch of proposed records before committing any of them. Nothing
becomes canonical without that approval; a review whose writes are never approved
still produced its verdict, it just leaves no trace for next time.

Running without a direct user channel (for example, inside a cold subagent) never
commits: emit the proposed distilled records as output instead, for the top-level
session to fold into its own close approval pass.

## Being invoked by another skill

Other skills may convene this panel by name instead of running their own review pass
(`plan-review` does, for load-bearing plans). When invoked this way, run `review <doc>`
as above and hand back the synthesized verdict, with any real-colleague attribution
in it still carrying the simulation label and mine date; the calling skill folds
blocking conditions into its own objection list. That attribution is for the chat.
The calling skill must not write any of it (names, labels, mine dates, panel
framing) into a repo artifact; per containment above, findings land there as plain
content only. Defer the close approval pass: a
panel invocation inside a calling skill's own review cycle does not run its own
close, it hands back the verdict and its proposed memory writes as output and holds
them until the calling skill's review terminates, then runs one close approval pass
covering that whole review (not one pass per panel invocation within it) — the
calling skill is responsible for actually running that pass when it terminates. If
this skill isn't installed, the caller degrades to whatever review it would
otherwise run — this skill has no required counterpart and works standalone.

Memory following the [follow-through](https://github.com/ConnorGriffin/follow-through)
pattern (skill owns workflow, data repo owns schema via its own `CONTEXT.md`) is an
optional upstream citation, not a dependency; nothing here requires that repository.
