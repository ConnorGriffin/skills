# ADR 65 — The code-discovery skill owns activation

Status: superseded by #300 (`codebase-memory` and `cbm-onboard` removed from the pack — see `openspec/changes/300-simplify-skill-pack/design.md`)

The public `codebase-memory` skill is the canonical source for its discovery hooks, settings registrations, standing instruction, and one installer command that activates them without clobbering existing configuration. Keeping the installer beside the skill gives every consumer one small interface and one implementation; machine repositories may invoke it, but must not reimplement its merge behavior or own divergent copies.
