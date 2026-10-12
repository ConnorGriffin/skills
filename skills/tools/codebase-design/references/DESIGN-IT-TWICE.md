# Design It Twice

When the user wants to explore alternative interfaces for a chosen deepening
candidate, use this parallel sub-agent pattern. Based on "Design It Twice"
(Ousterhout) — your first idea is unlikely to be the best.

Uses the vocabulary in [../SKILL.md](../SKILL.md) — **module**, **interface**,
**seam**, **adapter**, **leverage**.

Offerable in two places: standalone, or mid-interview as a grounding step —
when a `/ticket triage` interview hits an interface-shape frontier question,
this can run right there to ground the question before re-asking it.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem
space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see
  [DEEPENING.md](DEEPENING.md))
- A rough illustrative code sketch to ground the constraints — not a proposal,
  just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and
thinks while the sub-agents work in parallel.

### 2. Dispatch parallel design alternatives

The coordinator supplies the design-agent model. Dispatch each alternative as a
read-only subagent with that model named on the dispatch.

Start alternatives 1, 2, and 3 before waiting on any of them. Each
worker receives its separate technical brief and one different constraint:

- Alternative 1: "Minimize the interface — aim for 1–3 entry points max.
  Maximise leverage per entry point."
- Alternative 2: "Maximise flexibility — support many use cases and extension."
- Alternative 3: "Optimise for the most common caller — make the default case
  trivial."
- Alternative 4, when applicable: "Design around ports & adapters for
  cross-seam dependencies."

Include both [../SKILL.md](../SKILL.md) vocabulary and CONTEXT.md vocabulary
in every brief. Each worker must not modify, patch, or stash.

Each worker outputs:

1. Interface (types, methods, params — plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md))
5. Trade-offs — where leverage is high, where it's thin

On one failed completion, resume that same subagent once (`SendMessage`). If it
still does not produce a successful result, mark that alternative unavailable. With two or more
successful alternatives, present and compare the available designs, naming every
unavailable alternative. With zero or one successful alternative, report that
the design-it-twice pass did not produce enough alternatives and return to the
interface-shape frontier; do not recommend a design.

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare
them in prose. Contrast by **depth** (leverage at the interface), **locality**
(where change concentrates), and **seam placement**.

After comparing, give your own recommendation: which design you think is
strongest and why. If elements from different designs would combine well,
propose a hybrid. Be opinionated — the user wants a strong read, not a menu.
