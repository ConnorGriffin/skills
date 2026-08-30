# Replace the self-contained work order with a thin execution lock

## Why

A ticket in an OpenSpec-backed repository carries two records of the same intent.
The change on the ticket branch — proposal, design, delta specs, tasks — is the
durable planning authority. The fenced `WORK ORDER` comment then copies much of
that material into `Context`, `Do`, and `Done when` so that a fresh `start`
session can execute without reading anything else.

Two authorities for one fact drift. An amendment to the change after the order
was posted leaves the tracker comment describing a plan that no longer exists,
and nothing in the workflow notices: `start` executes the copy. Authoring and
reviewing both artifacts costs twice, and the second copy is the one that goes
stale.

The tracker comment does own facts the change record cannot: explicit human
authorization to execute, which revision is authorized, session and model fit,
execution shape and chunk ownership, verification, review depth, the expected
diff, and the stop-at-pull-request boundary. The seam runs between durable
change specification and execution authorization, not through either one.

## What changes

- The work-order template defines a versioned **execution lock** envelope with
  three source modes — `openspec <change-path>@<full-commit-oid>`,
  `repository-native <path>@<full-commit-oid>`, and `inline` (today's self-contained
  payload) — in both flat and chunked sub-lock shapes. One protocol, not a
  format per repository convention.
- Triage in an OpenSpec repository authors the change, validates it strictly,
  commits it on the ticket branch, and posts a lock pinning that full commit,
  selecting tasks and acceptance anchors positionally against the pinned bytes.
- `start` and `revise` fail closed before implementing or dispatching: an
  unrecognized version or source mode, an abbreviated or unresolvable OID, a
  source path absent at the pinned tree, an archived or invalid change, a
  missing selected task or acceptance anchor, a ticket branch that does not
  contain the pinned commit, or a source amendment with no newer lock each
  refuse and route to attended re-triage.
- The locator recognizes both protocols, newest recognized lock wins, and
  fields are never merged across comments. Already-posted `WORK ORDER`
  comments keep executing under today's sufficiency rules, with no inferred
  pin and no sunset.
- Orchestrate's `ORDER.md` carries the complete lock or sub-lock as an
  uncommitted transport copy that is never a second authority; a worker that
  cannot read the pinned source stops rather than continuing from memory.
- Epic-child handoff wording keeps the issue-body parent-plan pin as untrusted
  intake and the posted lock as the only authorization.

The change is prose contracts plus their pinning tests. No runtime code, no CI
workflow, and no OpenSpec adoption tooling changes.

## Risk contract

- **Must prevent:** silent execution of an unauthorized or amended source — a
  wrong commit, an archived change, or expanded scope; secret exposure; silent
  incorrect success.
- **Must recover:** nothing automatically. Validation failures stop cleanly.
- **Accepted failure:** a stale or invalid pin refuses execution with a clear
  message and routes to attended re-triage.
- **Unsupported:** retrofitting pins into already-posted legacy orders;
  multi-operator concurrent edits to one active change.
- **Evidence owed:** lock recognition and parsing, the fail-closed validation
  matrix (missing, stale, amended, archived, invalid source), the legacy-order
  path, and chunk sub-lock standalone sufficiency — through the existing test
  suites plus `scripts/validate.py` and strict OpenSpec validation.
