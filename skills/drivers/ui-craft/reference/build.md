# Mode: build

Assemble a greenfield surface's **locked screens** in the app from the approved
component library, in the build ticket the lock gate filed. The lock doc is the
whole contract: the build is checked against it and nothing else. A shipped
surface uses `revise` instead.

Input: the lock doc, its `Approved screens` with their locked canvas URLs, and
the merged library. Build only screens marked locked. Building from a draft is
how decisions get made in private.

## Before writing code

1. Read [web-implementation.md](web-implementation.md).
2. Branch from a freshly fetched default branch, and record the base SHA in the
   PR.
3. Read the lock doc end to end. List each place where it disagrees with the
   app's existing design system, and anything the build needs that the lock
   does not list. Stop and ask about every item. Never resolve one by
   implementer judgment.
4. Build or extend fixtures until every state in `States` renders. A fixture
   that cannot reach a state cannot prove it.

## While building

- Assemble each screen from the library's approved components and the lock's
  `Tokens`. A screen that seems to need a new component or a one-off variant
  stops the build: it is an inventory amendment and a `library` batch, never a
  build choice. On the plain-DOM path, build with the app's own markup and the
  lock's `Components` sizes.
- Treat the canvas as a picture of the target, not code to transplant.
- Every label reads a backend field listed in `Served vocabulary`. A label the
  backend does not serve is a lock amendment, not a build choice.
- The ported code is fed a payload from across a process boundary, not a
  fixture. Guard what it dereferences, and route failures into the screen's
  error state the lock describes. Do not invent states the lock lacks.
- A lock term that cannot be built as written stops the work. The operator
  rules on it, and the ruling lands as a dated `Amendments` line in the same
  change.

## Verify against the lock

Use the rendered verification in [tools.md](tools.md).

1. Render every approved screen, at every frame, in every state the lock lists.
   Use manufactured data, in both themes where the app has two.
2. Save each rendered page's HTML, declaring its frame per
   [lock.md](lock.md)'s precheck conventions, and run `precheck.py` on it. Run the
   overflow and button-height measurement too.
3. Compare each render, side by side, with the screen's locked canvas
   artboard at the same frame and state. Any difference is a finding until
   the operator rules on it. Check that each interaction map row works with
   touch and with pointer or keyboard.
4. Hand a fresh verifier subagent ([tools.md](tools.md)) only the lock doc and
   the renders. The builder never grades its own build.

## PR evidence

- Render pairs, locked canvas artboard beside the build, for each approved
  screen, frame, and state, from manufactured data;
- the full `precheck.py` output;
- the verifier's findings and how each was closed;
- the base SHA and data provenance;
- every `Amendments` line the build caused.

After merge, set the surface's `mockups/INDEX.md` line to `shipped`. Later
changes to the surface use `revise`.
