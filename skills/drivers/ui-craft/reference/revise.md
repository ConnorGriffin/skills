# Mode: revise

Change a surface the app already ships by editing the running app on a branch.
**Never rebuild a shipped surface as a from-scratch mock** (ADR 48). In the app,
a behavior survives unless the diff deletes it. In a mock, a missing behavior
leaves no trace for anyone to review.

The contract is the lock doc, including its **Must survive** list: at most one
page, one line per behavior, each saying where a render shows it. Rendered
before and after evidence checks that list. There is no replay script and no
per-story ledger. A fix with no lock doc still writes that list, in the PR.

Read [web-implementation.md](web-implementation.md) before changing CSS or
JavaScript/TypeScript.

## 0. Prove the app is safe to start

Iterate on the app only when the repo's `CLAUDE.md`/`AGENTS.md` declares two
things:

1. the exact dev-server command; and
2. the data source it reads, which must be a manufactured fixture or a
   synthetic database.

If that declaration is missing, incomplete, or ambiguous, stop and name what is
missing. Do not start the app to find out what it reads, and do not improvise
an entrypoint. A command that may read real, production, or vendor data is
unsafe. Record the quoted command and the named data source in the PR.

## 1. Base and before renders

1. Cut a worktree from the exact tip of a freshly fetched default branch, and
   record the base SHA.
2. Serve the base from a second fresh worktree, on a different port with the
   same data.
3. Render every screen, state, frame, and theme the change touches.

A second route inside the revision branch is not a comparison: it duplicates
the surface. Those renders are the "before" half of the evidence.

## 2. Iterate the running app

Work in short rounds:

1. Change the branch, using the app's own tokens, components, and chart library.
   A rewrite in place assembles its locked screens from the approved library
   and compares them with the locked canvas, as `build` does.
2. Render the affected states and frames, and run the
   [tools.md](tools.md) browser pass.
3. Run `precheck.py` on the saved rendered HTML.
4. Compare against the before renders and the lock.

In interactive work, take the running branch to the operator after each round.
Directions explored on a canvas during `lock` are wireframes. Lift the
decisions into the branch, never their code.

## 3. Must-survive behaviors

Each line on the list stays visible in an after render. A gesture or live
interaction counts only when exercised in the browser. Anything else is a
change the operator rules on, recorded as a dated `Amendments` line:

- **Dropped:** the operator's ruling and reason are quoted. The line leaves the
  list in the same change.
- **Changed:** the line is rewritten, and the after render shows the new
  behavior.
- **Moved to another surface:** name where it went, and update both surfaces'
  lists. A move looks like nothing happened, which is why it needs a record.
- **Renamed:** the glossary changes, and the old name is searched across the
  whole repository, not just this directory. Names outlive the code that
  introduced them.

A dropped, changed, or moved behavior without its amendment blocks the PR.

## 4. PR evidence

- Before and after render pairs for every affected screen, state, frame, and
  theme, from the same safe data;
- the must-survive list with the render or live check that proves each line;
- the full `precheck.py` output;
- the base SHA, the quoted safe-start command, and the data source;
- every `Amendments` line.

Review the running app, not only the source. Run the repo's persona sweep when
one exists, then `review`.
