"""Hand-maintained skill relationships, grounded in README and SKILL.md prose."""

RELATIONSHIPS = {
    "implement": {"uses": ["tdd", "code-review"], "requirements": "`tdd` and `code-review` from this pack"},
    "openspec-adopt": {"uses": [], "requirements": "GitHub CLI; global `@fission-ai/openspec@1.11.0`"},
    "ticket": {"uses": ["plan-review", "code-review"], "requirements": "GitHub CLI for the bundled issues binding, one binding page per other tracker; composes with `plan-review`, `code-review`"},
    "ui-craft": {"uses": [], "requirements": "Claude Code's Design and Design System artifact types, or plain artifacts, for canvases; Claude in Chrome or the built-in browser for rendered checks; subagent support for the cold critique"},
    "ci-design": {"uses": [], "requirements": ""},
    "code-review": {"uses": [], "requirements": "Parallel-agent support recommended; GitHub CLI to fetch an originating issue; see [docs/review-round-mining.md](docs/review-round-mining.md) for the mined evidence behind the fix protocol and the round cap"},
    "codebase-design": {"uses": ["domain-modeling"], "requirements": ""},
    "domain-modeling": {"uses": ["codebase-design"], "requirements": ""},
    "handoff": {"uses": [], "requirements": ""},
    "plan-review": {"uses": [], "requirements": "Parallel-agent support recommended; the round-count evidence behind its rules is in [docs/review-round-mining.md](docs/review-round-mining.md)"},
    "prototype": {"uses": [], "requirements": ""},
    "research": {"uses": [], "requirements": ""},
    "say-less": {"uses": [], "requirements": "Optional prompt hook for always-on digest; see [docs/overlay.md](docs/overlay.md) and the [measured comparison](docs/before-after.md)"},
    "tdd": {"uses": [], "requirements": ""},
    "writing-for-agents": {"uses": [], "requirements": "Hand-only; invoke by name"},
}
