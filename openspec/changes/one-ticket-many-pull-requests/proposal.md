# One ticket, many pull requests

## Why

Triage keeps asking the operator whether to split a ticket into child tickets
whenever the work spans repos, needs several pull requests, or follows a UI lock.
The operator declines every time. A ticket describes the work, not how many pull
requests land it. The working answer has been one lock per pull request on the
same ticket, each with its own `Expected diff` boundary, and the skills should do
that without asking.

## What changes

* Triage keeps multi-repo, multi-pull-request, and oversized work on one ticket.
  It posts a pieces checklist and locks one piece at a time. It never asks whether
  to split, and files child issues only when the operator asks.
* Triage locks the next open piece without asking once the current lock's pull
  request has merged.
* Finalize ticks the merged piece, leaves the ticket open while pieces remain, and
  closes it after the last one.
* UI Craft hands a locked surface to a build work order on the same ticket instead
  of a separate build ticket. The charter's UI line matches.

## Risk contract

* **Must prevent:** a ticket closing while a checklist piece is unbuilt.
* **Must recover:** none.
* **Accepted failure:** a ticket that tracks child issues from before this change
  keeps the child-issue path until it closes.
* **Unsupported:** one lock that spans several pull requests.
* **Evidence owed:** the UI Craft lock-handoff test pins the new wording.
