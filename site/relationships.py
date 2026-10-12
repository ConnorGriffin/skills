"""Hand-maintained skill relationships, grounded in README and SKILL.md prose."""

RELATIONSHIPS = {
    "implement": {"uses": ["tdd", "code-review"], "requirements": "`tdd` and `code-review` from this pack"},
    "openspec-adopt": {"uses": [], "requirements": "GitHub CLI; global `@fission-ai/openspec@1.11.0`"},
    "ticket": {"uses": ["plan-review", "code-review", "reviewer-memory"], "requirements": "GitHub CLI for the bundled issues binding, one binding page per other tracker; composes with `plan-review`, `code-review`; `reviewer-memory` from this pack"},
    "ui-craft": {"uses": [], "requirements": "The harness's built-in browser or preview tool for rendered review; parallel-agent support is recommended"},
    "ci-design": {"uses": [], "requirements": ""},
    "code-review": {"uses": ["reviewer-memory"], "requirements": "`reviewer-memory` from this pack; parallel-agent support recommended; GitHub CLI to fetch an originating issue; see [docs/review-round-mining.md](docs/review-round-mining.md) for the mined evidence behind the fix protocol and the round cap"},
    "codebase-design": {"uses": ["domain-modeling"], "requirements": ""},
    "domain-modeling": {"uses": ["codebase-design"], "requirements": ""},
    "handoff": {"uses": [], "requirements": ""},
    "plan-review": {"uses": ["reviewer-memory"], "requirements": "`reviewer-memory` from this pack; parallel-agent support recommended; the round-count evidence behind its rules is in [docs/review-round-mining.md](docs/review-round-mining.md)"},
    "prototype": {"uses": [], "requirements": ""},
    "research": {"uses": [], "requirements": ""},
    "reviewer-memory": {"uses": [], "requirements": ""},
    "say-less": {"uses": [], "requirements": "Optional prompt hook for always-on digest; see [docs/overlay.md](docs/overlay.md) and the [measured comparison](docs/before-after.md)"},
    "tdd": {"uses": [], "requirements": ""},
    "writing-for-agents": {"uses": [], "requirements": "Hand-only; invoke by name"},
}
