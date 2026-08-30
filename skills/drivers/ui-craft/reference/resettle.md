# Mode: resettle

Amend a locked term. This is the only legitimate path for changing anything a
lock manifest lists — including genuine improvements discovered mid-build.

`revise` has no lock manifest, so behavior changes on a shipped app branch do
not come here unless they also amend a still-binding legacy lock term. `revise`
records added, changed and retired behavior directly in the frozen behavior
ledger, with the same dated sanction rules. Never invent a term merely to route
an app revision through `resettle`.

A re-settle is sanctioned by the user (interactive) or, in headless runs, by
an explicit instruction in the work order. An agent may *propose* one at any
time; it may never *apply* one on its own judgment.

## A post-lock `missed` verdict lands here

When `behavior-sweep`'s predecessor inventory ([behavior-sweep.md](behavior-sweep.md)
§2) returns a `missed` verdict on a lock that has already merged — a shipped
behavior the lock neither kept nor sanctioned as retired — **this is the path**,
whether it surfaced during the build, in an audit, or by eye on a screenshot.
It is not a build call and not a bug fix: the merged lock currently says the
behavior is gone, so restoring it quietly is the private arbitration the lock
exists to forbid, and dropping it quietly is the original defect a second time.

This is also where the pass lands when it runs late — against a lock that closed
before anyone was looking backwards. Expect a pile rather than a row: the first
predecessor inventory run against a merged 60-term lock returned 43 unruled
retirements, one drawn selection window accounting for seventeen of them.

The operator rules it, and the ruling lands as one of two change sets:

- **kept** — re-settle the terms that have to describe the behavior. Usually
  there is no row to amend, because the lock was silent about it; then the
  re-settle **adds** the term and says in the mock header's `RE-SETTLED TERM`
  block that it restores a predecessor behavior the lock omitted. The behavior
  ledger gains its STORY and the replay script its function, in the same set.
- **retired** — no term moves. The behavior ledger gains its RETIRED entry and
  the replay script its absence assertion, to `behavior-sweep`'s enumeration of
  what a retirement owes; this page adds nothing to that list.
  Where the merged lock already spoke to the retirement, that citation rides
  along as the row's `ruled-elsewhere` annotation and nothing more: it is what
  turns the ruling into a one-sentence confirmation instead of a fresh decision,
  and it is never the sanction itself.

Either way it is dated and recorded, and the ledger keeps the trail.

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
   - the surface's **behavior ledger** (`mockups/<surface>.behavior.md`) if any
     story cites the term — rewrite the entry and record the reason under its
     `★ FROZEN` header, since the freeze pins a contract that would otherwise go
     silently stale. A mid-build resettle that leaves the frozen ledger untouched
     is incomplete. **RETIRED entries are amended in place, never deleted**: a
     reinstated behavior moves back to STORY in this change set and its
     retirement stays visible above it as the record of what was reversed;
   - `mockups/INDEX.md` if the surface's status or files changed (columns
     Surface / Concept / Status / Issue / File) — it registers the behavior
     ledger and the sweep-evidence directory `mockups/sweep/<surface>/` too.
3. If the term had a `LOCK:` assertion, update the assertion in the same
   change and prove the new one can fail.
4. If a build is in flight, update its fidelity ledger row from
   `re-settle requested` to `met` with the new evidence.

A re-settle that touches only the code, or only the mock, is incomplete —
the header, manifest, assertions, and siblings move together or the lock is
in an inconsistent state that some future build will arbitrate in private.
