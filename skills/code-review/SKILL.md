---
name: code-review
description: Review the changes since a fixed point (commit, branch, tag, PR, or merge-base) on two axes — Standards (does it follow this repo's documented rules?) and Spec (does it do what the originating issue asked?). Each axis returns a verdict per enumerated item rather than an open-ended list of findings, so a round terminates. Use when the user wants to review a branch, a PR, working-tree changes, or asks to "review since X"; and again after fixes, to review the fix.
---

# Code review

Review a diff on two axes, in parallel sub-agents, and report them side by side.

- **Standards** — does the code follow the rules this repo documents?
- **Spec** — does the code do what the originating issue or plan asked for?

The premise that makes this different from "find problems in this diff": **a
review round has to be able to finish.** An open-ended hunt samples a diff, and
every fresh round samples it differently, so three rounds turn up three disjoint
sets of real defects and nobody can tell whether the fourth would turn up more.
Each axis here enumerates a closed list from a source document first, then
returns a verdict per item. Findings are the items that came back bad. The
reader learns what was checked, not just what was noticed.

Two rules follow from that, and they are the ones to keep if everything else is
forgotten:

1. **Enumerate before you judge.** The list of things to check comes from a
   document (the repo's standards, the issue's acceptance criteria), so it is
   finite, and the same on every run.
2. **A finding carries a failure scenario.** Concrete input or state, traced in
   the code, and the wrong thing that results. No scenario means it goes in
   `unverified` or is dropped. A plausible-sounding finding nobody traced is how
   a fix gets written for a defect that was never there.

## Modes

**First review** — the full process below.

**Re-review** (after fixes land): the diff under review is *the fix*, not the
original change. Run the same two axes over it, with one extra question per
fixed finding: does the fix do what the finding asked, **and does it contradict
anything the original code or its documents already said?** This mode is not
optional politeness. A fix written from the finding text rather than from the
code is the single most reliable source of new defects, because the author has
the finding in front of them and not the system. Scope the divergent-copies check
to the fix: enumerate the copies of every fact the fix touched, and return a
verdict per pair. A fix that edits one copy of a fact with four encodings has
minted three new pairs that can disagree, and the next round will find one.

**Hard cap: three rounds.** If round 3 still returns new violated items on the
same enumeration, the change has a structural problem, not undiscovered typos —
almost always a fact with too many copies, or logic that exists only as prose.
Stop reviewing. Name the structure problem and route it to the author as a design
decision. A fourth fix round on the same enumeration buys new defects, not fewer.

## Fixing findings

Rules for the change's author, not for the reviewing session — a review still
only finds, and hands these to whoever holds the code. This is where rounds are
manufactured.

1. **Re-derive the fix from the code and its documents, never from the finding
   text alone.** The finding names the symptom; the code owns the truth. Open the
   file, read what is actually there, and decide the fix from that. Patching the
   sentence or line a finding quotes, without re-reading what surrounds it, is how
   a round's worst defect ends up authored by the previous round's fix.
2. **A fix that touches a fact with copies updates every copy, or collapses them
   to one authority — and says which it did.** Half a fact updated is worse than
   none: it converts a redundancy into a contradiction.
3. **When a finding cites a rule with a rationale, sweep the diff for every other
   site that rationale covers before declaring it fixed.** One measured fix
   applied a case-insensitivity correction to 1 of the 3 regexes that shared its
   reason, and the other 2 cost a further round.
4. **A fix that edits prose triggers a re-read of the surrounding section**, for
   sentences the edit now contradicts. Prose has no compiler; the only check on a
   documentation fix is the paragraphs it sits inside.

## Process

### 1. Pin the fixed point

Whatever the user named is the fixed point: a SHA, branch, tag, `main`, `HEAD~5`,
a PR URL or number, or nothing (meaning the working tree against `HEAD`).

For a PR, fetch it rather than trusting the local checkout:

```bash
git fetch origin pull/<n>/head:pr-<n> && git fetch origin <base>
```

Then resolve and **check the base is not stale**:

```bash
git rev-parse <fixed-point> && git rev-parse origin/<fixed-point>
```

If a local branch and its remote differ, use the remote. A local `main` that is
five merges behind silently pulls other people's commits into the diff and every
finding against them is noise. Confirm the diff is non-empty before spawning
anything; a bad ref should fail here, not inside two sub-agents.

Record once: the diff command (`git diff <base>...<head>`, three-dot) and the
commit list (`git log <base>..<head> --oneline`).

### 2. Build the Standards enumeration

Collect what this repo documents about how code is written: `CONTRIBUTING.md`,
`CODING_STANDARDS.md`, `AGENTS.md` / `CLAUDE.md`, `README.md`, any `docs/`
convention file, and the linter config. **Read them at the head of the diff**,
not on the current checkout, so you judge against the version the change lands.

From those, write the enumeration: the specific documented rules this diff could
plausibly breach. Ten to twenty is normal. A rule nothing in the diff could
touch is left out, and the sub-agent is told how many were left out.

Then add these three, which apply even to a repo that documents nothing:

- **Divergent copies.** Which facts does this change write down in more than one
  place, and do the copies agree? Count every encoding: code, config, workflow
  conditions, generated output, and prose in documents. This is the highest-yield
  check in the set. A fact with N copies has N(N-1)/2 pairs that can disagree,
  none of them checked by anything, and each review round finds a different pair.
  Where the copies are already many, the finding is the redundancy itself, not
  the one pair that happens to disagree today.
- **Claims nothing can falsify.** Does the change add prose asserting what the
  code does, with no test that fails when the two disagree? Name the sentence.
- **Guards for unreachable states**, and their inverse: a trust boundary
  (external input, cross-process data, durable state) crossed with no guard.

Skip anything the linter or formatter already enforces. Reporting what CI
already fails on wastes the round.

### 3. Build the Spec enumeration

Find the originating spec, in order:

1. Issue or ticket references in the commit messages or PR body (`#123`,
   `PROJ-4567`, `Closes #45`) — fetch it. If the repo documents its tracker,
   follow that; otherwise infer from the git remotes.
2. A path the user passed.
3. A plan under `openspec/`, `docs/`, `specs/`, or `.scratch/` matching the
   branch or feature. An archived plan added by the diff itself still counts.

The enumeration is that document's **acceptance criteria**, one line each,
verbatim. If it has a tasks list, that is the enumeration.

If the change wires into another component or skill, the **integration contract**
joins the enumeration: who calls whom, and at which point. A change reviewed only
in isolation passes clean and then spends the next round on nothing but seam
defects.

If no spec exists, skip the Spec sub-agent and say so in the report. Do not
substitute the PR description written by the same author as the code.

### 4. Run both axes in parallel

Two sub-agents, one message, `general-purpose` for both. Each gets: the diff
command, the commit list, its enumeration, and its brief.

**Shared brief** — give this to both:

> Trace every claim to the code before reporting it. For each finding state a
> failure scenario: the concrete input or state, and the wrong output, crash, or
> false statement that results. If you cannot construct one, put the item under
> `unverified` instead of `findings`. Do not report anything the linter
> enforces. Do not report style preferences the repo has not written down. Any
> executable literal in the diff or its documents — a regex, a shell fragment, a
> workflow expression, a query — is verified by executing it against a real
> input, never by reading it. Under 400 words.

**Standards brief:**

> Here is the enumeration of documented rules this diff could breach, plus the
> three general checks. Return a verdict for every item: holds / violated /
> not applicable, with the file and line for anything violated, and the rule you
> are citing. Then, and only if any would change whether this merges, up to
> three additional observations not on the list. State how many items you
> checked.

**Spec brief:**

> Here is the enumeration of acceptance criteria, verbatim. Return a verdict for
> every one: met / partial / unmet / not verifiable from the diff, quoting the
> criterion and naming the code or test that settles it. Then report behaviour
> in the diff that no criterion asked for (scope creep). Do not re-litigate
> decisions the plan already settled, and do not report unticked checkboxes as
> findings — an unchecked box for work the plan defers is not a defect. State
> how many criteria you checked.

### 5. Aggregate and report

Present the two verdict sets under `## Standards` and `## Spec`, verbatim or
lightly cleaned. **Do not merge or rerank across axes** — see *Why two axes*.

Lead each axis with its coverage: "18 rules checked, 2 violated". Coverage is
what tells the reader the space was enumerated rather than sampled, and it is
the number that makes a clean round mean something.

List `unverified` items separately and briefly, if any. They are not findings.
They are the honest residue, and naming them stops a later round from
re-deriving the same suspicion as if it were new.

End with one line: findings per axis, and the worst issue *within each axis*.
Never pick a single winner across axes.

### 6. Say whether it is done

Close with the termination state, explicitly:

- **Converged** — every enumerated item holds or is met, and any prior round's
  findings were re-reviewed and confirmed fixed.
- **Not converged** — name what is outstanding.
- **Capped** — round 3 returned new violated items on the same enumeration.
  Name the structural problem behind them and hand it to the author as a design
  decision. This state ends the review; it is not an invitation to round 4.

A re-review that returns no new violated items on the same enumeration is the
signal to stop, and the skill should say so rather than leaving the reader to
guess whether another round would find more.

## Reporting rules

- Anchor every finding to `file:line`.
- Quote the rule or criterion. A finding that cannot cite one is an opinion, and
  belongs in the capped observations, not in the verdicts.
- Say what breaks, not what is inelegant. "Returns None and the caller never
  sees the failure" beats "swallows the error".
- A fix suggestion is one line. The review's job is to find, not to rewrite.

## The smell checklist

Consult while judging; report only what passes the gate in the Standards brief
(would it change whether this merges?), capped at three. These are heuristics,
never hard violations, and a documented repo standard always overrides one.

Mysterious Name (name doesn't reveal what it does) · Duplicated Code (same shape
twice) · Feature Envy (method reaching into another object's data) · Data Clumps
(same fields travelling together) · Primitive Obsession (string standing in for
a domain concept) · Repeated Switches (same cascade on the same type) · Shotgun
Surgery (one change, scattered edits) · Divergent Change (one file edited for
unrelated reasons) · Speculative Generality (abstraction for needs the spec
doesn't have) · Message Chains (`a.b().c().d()`) · Middle Man (mostly delegates)
· Refused Bequest (implementer ignoring most of what it inherits).

## Why two axes

A change can pass one and fail the other:

- Follows every standard, implements the wrong thing → Standards pass, Spec fail.
- Does exactly what the issue asked, breaks the project's conventions → Spec
  pass, Standards fail.

Reporting them separately stops one axis from masking the other. It also stops
the aggregation step from quietly dropping the axis with fewer findings, which
is what reranking into a single list does.
