# Mode: resettle

Amend a locked term. This is the only legitimate path for changing anything a
lock manifest lists — including genuine improvements discovered mid-build.

A re-settle is sanctioned by the user (interactive) or, in headless runs, by
an explicit instruction in the work order. An agent may *propose* one at any
time; it may never *apply* one on its own judgment.

## Steps

1. Name the term (manifest number), the change, and who sanctioned it.
2. Update, in one change set:
   - the mock header — a dated `RE-SETTLED TERM` block quoting the old term,
     the new term, and the sanction ("supersedes …", the existing repo
     convention);
   - the **manifest** — rewrite the term row, and fixture obligations or
     verbatim strings if they moved;
   - sibling locked artifacts the term appears in (the other form factor's
     mock, a copy spec) so the locked set stays self-consistent;
   - `mockups/INDEX.md` if the surface's status or files changed (columns
     Surface / Concept / Status / Issue / File).
3. If the term had a `LOCK:` assertion, update the assertion in the same
   change and prove the new one can fail.
4. If a build is in flight, update its fidelity ledger row from
   `re-settle requested` to `met` with the new evidence.

A re-settle that touches only the code, or only the mock, is incomplete —
the header, manifest, assertions, and siblings move together or the lock is
in an inconsistent state that some future build will arbitrate in private.
