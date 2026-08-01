# Mode: build

Implement a locked visual spec. The finish line is **every manifest term has
evidence** — not "the gates are green". A build that passes every test while
diverging from the lock is a failed build.

Input: the ★ LOCKED mockup(s) and `mockups/<surface>.lock.md`. If the
manifest is missing, stop and create it first (run the manifest-extraction
part of `lock` mode against the existing header — do not build from prose).

## Before writing code

1. Read the manifest, the mock headers, and the mock's **component CSS** —
   not just its layout. Diff the mock's component styling (buttons, chips,
   rows) against the app's shipped equivalents; where they differ, the
   manifest's precedence line decides. List the differences you will honor.
2. If any two locked artifacts contradict each other, or a locked term
   collides with the design system beyond what precedence settles: **stop and
   surface it.** Implementer arbitration is how locks die.
3. Read the fixture obligations. Build or extend fixtures until every locked
   visual feature actually renders under them. A tame fixture that leaves a
   ribbon invisible or a threshold untriggered cannot prove anything.

## While building

- `design-rules.md` governs craft; the manifest governs content. Where they
  disagree, the manifest wins — improvements to a locked surface go through
  `resettle`, even mid-build, even when the improvement is real.
- Every `gate` term gets an assertion in the rendered browser gate, tagged
  with its manifest number in a comment (`// LOCK:<surface>:<n>`), so
  coverage is greppable.
- **Prove each lock assertion can fail.** Once per assertion: knock the
  feature out, watch the assertion go red for the right reason, restore.
  This is the charter's "failed first" applied to visual gates; it is what
  catches operator-precedence truthiness, wrong-state fixtures, and
  screenshots of nothing.
- **Rewriting a test file transfers its invariants.** Before replacing any
  rendered gate, list the assertions the old file made; every one either
  reappears in the new file or is named as dropped (with why) in the PR.
  Silently dropped assertions are how locked terms become untested.

## The fidelity ledger

The PR ships a ledger — in the PR body or `docs/` — one row per manifest
term:

```markdown
| # | Term | Status | Evidence |
|---|------|--------|----------|
| 1 | No page scroll at 1280x800 | met | LOCK:settings-audit:1 assertion |
| 3 | Excursion aligns with block | met | paired render R3 |
| 7 | Meal blocks colour-washed | re-settle requested | see PR comment |
```

Statuses: `met`, `re-settle requested` (with the resettle recorded), or
`blocked` (with why). There is no "partially" and no silent omission — a term
absent from the ledger is a blocking gap.

## Paired renders

For every `eye` term and every state the manifest names: render the **locked
mock** and the **built surface** side by side, same fixture, same viewports,
and attach the pairs to the PR as the charter's proof-of-match. A screenshot
of the build alone proves nothing; the pair is what makes drift visible to a
reviewer who can't execute the spec. Verify each pair actually exercises its
term before attaching (fixture obligations again).

## Review handoff

Give the cross-reviewer the manifest, the ledger, and the paired renders —
their checklist is the manifest, not the diff. "Does render N match mock N on
terms X, Y, Z" is an answerable question; "read this HTML comment" was not.
