# Engineering charter

Standards every app built in this flow must meet. Read by **both** tools
(Claude via `CLAUDE.md`, Codex via `AGENTS.md` — the *same canonical bytes*)
and enforced at review: a violation below is a blocking finding.

> Seed — refine it. This is the bar, not holy writ.

## Architecture — deep modules

- Every module's **interface is far simpler than its implementation.** A module whose
  interface is nearly as complex as its body is *shallow* — deepen it or delete it.
- Apply the **deletion test:** if removing a module just moves complexity around
  rather than concentrating it, it shouldn't exist.
- **The interface is the test surface.** Don't extract pure functions "for
  testability" when the real bugs live in how they're called — preserve **locality**.
- Use the vocabulary exactly — module / interface / depth / seam / adapter / leverage
  / locality (`/codebase-design`). **One adapter = a hypothetical seam; two = a real
  one** — don't build the seam before the second caller exists.

## UI — never invented at build time

- Any user-facing surface goes through **`/ui-craft lock` to a *locked* visual
  spec** before it is implemented — a ★ LOCKED mockup **plus its lock manifest**
  (`mockups/<surface>.lock.md`: numbered gate/eye terms, a precedence line for
  design-system conflicts, fixture obligations, verbatim strings). No ad-hoc UI.
- Implementation runs as **`/ui-craft build`**: the manifest is the contract.
  Locked-artifact contradictions are surfaced, never arbitrated in private;
  deviations go through `/ui-craft resettle`, never a quiet diff; every `gate`
  term gets a rendered assertion that has been **shown to fail** when its
  feature is knocked out; replacing a test file transfers its assertions or
  names the drops in the PR.
- A PR that changes a user-facing surface attaches **paired mock-vs-build
  screenshots** (headless Playwright, same fixture and viewports — fixtures
  must actually exercise the locked visuals) and a **fidelity ledger** walking
  every manifest term to `met` / `re-settle` / `blocked` — the unattended
  stand-in for a live demo.
  A UI change missing the pairs or the ledger is a **blocking** gap, not a nit.
  Green gates are not the finish line; the walked manifest is.

## The pull request — framed for the human who merges

- **The PR body is written for whoever merges it, in plain language:** what changed,
  why, and what to check — in the app's own domain terms (**`CONTEXT.md`**), not the
  implementation. The PR already *is* the diff; don't narrate it in code.
- **No jargon:** a body that leans on file / function / test names or CSS / API
  specifics instead of app behavior can't be merged at a glance — that's a
  **blocking** gap, not a nit.

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
- **ADR identity comes from the originating tracker item.** New records use
  `docs/adr/adr-<issue>-<slug>.md` with heading `# ADR <issue> — Title`, where
  `<issue>` is the id of the issue, ticket, or PR that originated the decision.
  Two records from one issue use distinct slugs. Existing sequentially numbered
  ADRs are legacy records: keep their names and links; do not add new ones in
  that format.
