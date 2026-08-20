# ADR 65 — The code-discovery skill owns activation

The public `codebase-memory` skill is the canonical source for its discovery hooks, settings registrations, standing instruction, and one installer command that activates them without clobbering existing configuration. Keeping the installer beside the skill gives every consumer one small interface and one implementation; machine repositories may invoke it, but must not reimplement its merge behavior or own divergent copies.
