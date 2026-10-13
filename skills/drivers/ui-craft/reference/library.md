# Mode: library

Build the lock's approved component inventory in the project's component
library, one component at a time, in its own ticket. This is the only code
written before a screen locks. It builds components, never screens.

Input: a lock doc whose `Components` inventory the operator approved, and whose
`Stack` names a library. A plain-DOM lock has no library stage.

## Before the first component

1. Read [web-implementation.md](web-implementation.md) and
   [tools.md](tools.md)'s library stack section.
2. With no component library in the repo, this ticket, the first code ticket,
   records the stack choice as an ADR in the repo's ADR home before the first
   component. Then scaffold the library and its story tooling.
3. Branch from a freshly fetched default branch.

## Each component

1. Build it with the lock's `Tokens` and its inventory entry's single size per
   role. Labels read only the fields its entry lists.
2. Write **one story per state** in the entry. Each story uses manufactured
   data and marks the precheck conventions in [lock.md](lock.md): the story
   root carries `data-screen` and `data-frame`, plus `data-label`,
   `data-value`, and `data-primary`.
3. Take **one screenshot per story**, at every frame where the component
   changes, using the rendered verification in [tools.md](tools.md).
4. Run `precheck.py` on each story's saved HTML, plus the browser pass. Then run
   a cold critique on the component's stories and screenshots
   ([tools.md](tools.md)). A failing check keeps the component out of the batch.
5. Check every gesture in the entry with touch, and with pointer or keyboard.

## Batches

Present components to the operator **in isolation, in batches of three to five,
never composed into a screen**. Each batch shows:

- each component's stories and screenshots;
- the precheck output;
- the critique's open findings.

A batch is a gate. Echo every comment back before acting, and run at most three
refinement rounds per batch. The operator's approval of each component is a
dated `Amendments` line, and its inventory entry gains `approved: <date>`.

A component the operator wants that the inventory lacks is an inventory
amendment first, then a component in a later batch.

When every component is approved, merge the library change, and the design
session resumes at sync ([lock.md](lock.md) §6).
