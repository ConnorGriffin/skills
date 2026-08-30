# Codify the revision round method in ui-craft

## Why

A UI revision that iterates in the running app while direction is still unsettled
does not converge. One attended revision session recovered by refusing the app,
diverging on paper, and narrowing one question per round — and then hit a second
class of failure once the surface actually moved: five gates red, none of them a
defect in the shipped app, every one a written record that did not move with the
behavior it described.

`ui-craft` already licenses throwaway wireframes for divergent work, but says
nothing about how the rounds are run, and its behavior ledger has no case for a
behavior that changes which surface owns it. A retirement's guard asserts the
absence it produced but not the premise it reasoned from, so a later change that
kills the premise passes silently.

## What changes

- `revise` §3 gains a round-running subsection, scoped to interactive divergent
  work and deferring to the existing headless rule: one narrowing question per
  round with nothing ruled reopening, conceptually distinct options each carrying
  a stated cost, measured rather than asserted claims, the operator's eye
  outranking a metric that measures the wrong thing, and building only once the
  direction is ruled.
- `revise` §4's behavior cases gain **Moved** beside Preserved / Added / Changed /
  Retired, with the same ceremony as a removal, plus the sweeps a move, a
  duplication or a rename owes outside the ledger.
- `revise` §5's before-landing checklist requires the story-replaying gates to
  have actually run for a round that moved a surface, launched by whoever can
  launch them.
- `behavior-sweep` §4's retired guard asserts the retirement's premise as well as
  the absence, and a failed premise is a QUESTION-round trigger rather than a
  `replayed-fail`; §5's worked example and `build`'s RETIRED replay enumeration
  follow.

The method binds through the skill pack, so every consuming repository inherits
it without an agent brief of its own. No mode, route, lock manifest, sanction
contract or headless rule changes.

## Risk contract

- **Must prevent:** silently weakening an existing `ui-craft` rule — the behavior
  ledger, the sanction line, the lock contract, or the headless restriction —
  while merging the new material; naming a consuming repository's internals in
  skill text.
- **Must recover:** none. Documentation-only and revertible by pull request.
- **Accepted failure:** the generalized wording misses a nuance of the session it
  came from; a follow-up round fixes it.
- **Unsupported:** binding workflows outside `ui-craft`; retroactive application
  to revisions already landed; changing the sanction line's named-person
  requirement.
- **Evidence owed:** a `tests/test_behavior.py` pin on the new subsection and the
  retired-premise rule across all three pages, proven to fail when the subsection
  heading is removed; OpenSpec strict validation, the structural validator, and
  the repository test command pass.
