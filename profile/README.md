# Shared profile

`base.md` and `CHARTER.md` are the machine-agnostic global-instructions layer,
meant to be `@`-imported from a local checkout on any machine (personal, work, ...).
Machine-specific details (tool availability, private repo paths, model prefs) stay
out of this repo, in each machine's own overlay.

## Setup

1. Clone this repo somewhere on the machine, e.g. `~/code/skills`.
2. In that machine's `~/.claude/CLAUDE.md` (or `AGENTS.md`), put the imports at
   the top, followed by the machine's private overlay:

   ```
   @/absolute/path/to/checkout/profile/base.md
   @/absolute/path/to/checkout/profile/CHARTER.md

   ## Overlay: <machine name>

   - Model prefs, tool availability, private repo paths, etc. — whatever is
     specific to this machine and shouldn't live in a public repo.
   ```

3. Repeat per machine, with a different overlay and the same two imports.

The base assumes this repo's skills (`/ui-craft`, `/codebase-design`, etc.) are
installed, but degrades fine without them — the charter still reads as plain
prose if the slash commands aren't available.
