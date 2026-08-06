# Engineering charter

Standards every app built in this flow must meet. Read by **both** tools
(Claude via `CLAUDE.md`, Codex via `AGENTS.md` — the *same canonical bytes*)
and enforced at review: a violation below is a blocking finding.

> Seed — refine it. This is the bar, not holy writ.

## Architecture — deep modules

- Every module's interface is far simpler than its implementation; a shallow
  module is deepened or deleted.
- The interface is the test surface: don't extract pure functions for
  testability at the cost of locality.
- Apply the **deletion test:** if removing a module just moves complexity around
  rather than concentrating it, it shouldn't exist.
- Use the vocabulary exactly — module / interface / depth / seam / adapter / leverage
  / locality (`/codebase-design`). **One adapter = a hypothetical seam; two = a real
  one** — don't build the seam before the second caller exists.

## UI — never invented at build time

- Every user-facing surface goes through the **`/ui-craft`** lock-then-build
  lifecycle: lock a visual spec before implementation, build against that lock,
  and attach fidelity evidence to the PR. The full rules (manifest format,
  resettle process, screenshot and ledger requirements) live with `/ui-craft`.

## The pull request — framed for the human who merges

- **The PR body is written for whoever merges it, in plain language:** what changed,
  why, and what to check — in the app's own domain terms (**`CONTEXT.md`**), not
  file / function / test names or CSS / API specifics. The diff already shows the
  implementation; a body that leans on it instead of app behavior is a **blocking**
  gap, not a nit.

## Testing — through the interface

- New behavior ships with a test that **exercises it through the public interface**,
  and — where it fits — one that failed first for the right reason.
- A green suite that doesn't exercise the behavior is not coverage.

## Maintainability

- **Match the surrounding code** — idiom, naming, comment density.
- **No dead code, no speculative abstraction.** Build the seam when the second caller
  is real, not before.
- **Earn every guard.** An edge case is real only when its state is reachable under the
  system's **enforced** invariants — *enforced* meaning the state is rejected or made
  unrepresentable before the guard, by code or by a pinned test; a comment or a survey of
  today's callers is not enforcement. Guards at a trust boundary are never speculative:
  external input, cross-process or cross-tool data, concurrent state, and durable state a
  crash, a human edit, or the clock can perturb — an illustrative list, not a closed one.
  Elsewhere, a guard for a state that cannot occur is complexity, not safety: adding one is
  a defect, and removing one is a legitimate fix **only when the removal names the enforced
  invariant** that makes the state unreachable. Keep every guard that acceptance criteria,
  security or adversarial input, or observed behavior grounds.
- Domain terms come from **`CONTEXT.md`**; record load-bearing, hard-to-reverse
  decisions as **ADRs** — and don't re-litigate settled ones.
- **An ADR's home is wherever the repo already records decisions.** A repo
  tracking design with OpenSpec records the decision in its change's
  `design.md` under a `## ADR <issue> — Title` heading (the change already names
  the work, so the issue id is the record's identity); do not add a parallel
  `docs/adr/` tree beside it. An established `docs/adr/` tree wins over
  OpenSpec: keep adding records where the history already is, rather than
  forking it. A repo with no existing home
  gets `docs/adr/adr-<issue>-<slug>.md`, heading
  `# ADR <issue> — Title`, where `<issue>` is the id of the issue, ticket, or PR
  that originated the decision. Two records from one issue use distinct slugs.
  Existing sequentially numbered ADRs are legacy records: keep their names and
  links; do not add new ones in that format.
