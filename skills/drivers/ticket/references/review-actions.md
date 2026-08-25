# Review actions

Ground each finding before choosing exactly one disposition.

* **Fix before completion.** It breaks the work order; fix and verify it in this
  pull request.
* **Necessary follow-up.** It is real but outside the order; file a ticket with
  evidence, desired outcome, and a checked duplicate search. Keep it out of this
  pull request. Under an epic, read
  [the epic tracker reference](../../epic/references/github-tracker.md): when the
  epic destination requires it, file the follow-up as an in-scope native child;
  otherwise file it as a native child with its `spike` or `build` type plus
  `deferred`, and report it on the originating ticket.
* **Ask the maintainer.** A real choice remains; surface it before editing.
* **Discard as preference.** It is unsupported reviewer taste; make no change and
  say why in the reply.
