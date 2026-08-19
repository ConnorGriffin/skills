---
name: handoff
description: Produce a decision-safe handoff for a fresh agent. Use when a task changes hands, a session is ending midstream, a user asks for a handoff, or an agent needs to preserve a design/map/implementation decision without making the next agent rediscover it.
---

# Handoff

Treat a handoff as a bounded state transfer, not a project report. Give the next agent the current decision, the evidence that makes it true, the safe first action, and the boundaries that prevent duplicate or contradictory work.

## 1. Establish the transfer

Identify the recipient and the job they are taking over. State whether the handoff is for a fresh agent, a later session, or a human decision.

Record the user's latest intent in their words where possible. Separate it from earlier superseded requests.

Finish when the receiving job is explicit and no longer depends on conversation archaeology.

## 2. Re-ground volatile state

Verify facts that may have changed: active agents and claims, issue or PR state, branch/worktree status, uncommitted files, and the latest rendered or test result. Do not carry forward status from memory.

Capture only artifacts the recipient needs, with exact paths or canonical issue/PR links. Mark each as committed, uncommitted, remote, local-only, retired, or merely referenced. Do not present an unpushed link as available work.

Finish when each material claim has a source the recipient can inspect.

## 3. Preserve decisions and boundaries

Write the settled decisions first. For each one, name its owner or source of truth and the consequence for the next agent.

Then record unresolved decisions as choices, not as accidental assumptions. If an ordering, authorization, product meaning, or dependency is genuinely undecided, make the first action a question or a safe investigation; do not choose silently.

List rejected, retired, or already-completed work that must not be repeated. Include domain vocabulary corrections that change implementation meaning.

Finish when the receiving agent can distinguish locked work from proposed work and pending work.

## 4. Give one safe first action

End with the next action that advances the task without reopening settled ground. If it is blocked by a user choice, say exactly what must be decided and why. Do not tell the recipient to “review the context” or “continue work.”

Finish when a fresh agent can begin productively from the handoff alone.

## Handoff shape

Use this shape; omit empty sections rather than adding filler.

```md
# Handoff — <recipient job>

## First action

<one safe, specific action; include the required user decision if blocked>

## Current decision

- <settled decision> — <source of truth>; <consequence>

## Evidence and artifacts

- [artifact or issue](https://example.com/artifact-or-issue) — <status and why it matters>

## Do not redo or assume

- <retired/completed/rejected work>
- <unresolved choice and its options>

## Safety and repository state

- <relevant hazards, claims, dirty-worktree or authority limits>
```

## Delivering it

**The handoff is the artifact. Write it to a file and hand over the path — nothing else.**

A handoff is written for the agent taking over, not for the person who asked for it. Asking to hand the work off means they are done reading. Summarizing the handoff back to them defeats the point: they read the same content twice, in the worse of the two formats, at the moment they were trying to stop.

The delivering response is one line — the path, plus the single fact only they can act on if one exists (an unmerged PR, a pending authorization). No section recap, no highlights, no "the parts you'd want to know", no bulleted extract of the file. If something genuinely cannot wait for the next agent, it belongs *in* the first-action section, not in a parallel chat summary.

This holds when the handoff is long and the urge to orient them is strongest. Length in the file is fine — it is written for a cold reader. Length in the response is not.

## Quality gate

Before delivering, verify that the handoff names the first action, distinguishes fact from proposal, links every material artifact, records volatile state as checked, and tells the recipient what not to repeat. Remove chronological narration, speculative detail, and generic next steps.

Then check the response itself: if it restates anything the file already says, cut it back to the path.
