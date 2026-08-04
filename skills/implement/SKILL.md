---
name: implement
description: "Implement a piece of work based on a PRD or set of issues."
---

Implement the work described by the user in the PRD or issues.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Before /review, run /simplify over the changed code.
<!-- simplify is deliberately not wired into the unattended build path (BUILD_PROMPT):
     unattended builds are budget-bound and simplify applies edits outside the diff. -->

Once done, use /review to review the work.

Commit your work to the current branch.
