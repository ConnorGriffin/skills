# Tasks

- [x] Rewrite triage's slicing step as sequenced locks on one ticket, and lock the
      next piece without asking after a merge.
- [x] Have finalize tick the merged piece and keep the ticket open while pieces
      remain.
- [x] Move UI Craft's lock handoff, library, and build wording from tickets to
      work orders, and update the charter's UI line and both site narratives.
- [x] Repoint the UI Craft lock-handoff and library-stack tests at the new wording.
- [x] Have triage lock every piece in one pass, with `Piece:` and `Waits on:` on each
      order, one branch per piece, locate by piece, and start refusing an order
      whose dependency has not merged.
