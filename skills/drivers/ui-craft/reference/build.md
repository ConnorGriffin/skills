# Mode: build

Implement a **locked** greenfield surface in the app, in the build ticket the
lock gate filed. The lock doc is the whole contract: the build is checked
against it and nothing else. A shipped surface uses `revise` instead.

Input: the lock doc with `Status: locked`, plus its canvas URL or reference
bundle. If the status is not locked, stop. Building from a draft is how
decisions get made in private.

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

- Build with the app's own components and the lock's `Tokens`. Treat the canvas
  as a picture of the target, not code to transplant. The Design type's export
  or handoff is a starting point at most, and it must end on the app's
  components.
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
2. Save each rendered page's HTML and run `precheck.py` on it. Run the
   overflow and button-height measurement too.
3. Compare each render with its approved screen. Check that each interaction
   map row works with touch and with pointer or keyboard.
4. Hand a fresh verifier subagent ([tools.md](tools.md)) only the lock doc and
   the renders. The builder never grades its own build.

## PR evidence

- One render per approved screen, frame, and state, from manufactured data;
- the full `precheck.py` output;
- the verifier's findings and how each was closed;
- the base SHA and data provenance;
- every `Amendments` line the build caused.

After merge, set the surface's `mockups/INDEX.md` line to `shipped`. Later
changes to the surface use `revise`.
