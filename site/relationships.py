"""Hand-maintained skill relationships, grounded in README and SKILL.md prose."""

RELATIONSHIPS = {
    "review": {"uses": ["code-review", "plan-review"], "requirements": ""},
    "implement": {"uses": ["tdd", "code-review"], "requirements": "`tdd` and `code-review` from this pack"},
    "openspec-adopt": {"uses": [], "requirements": "GitHub CLI; global `@fission-ai/openspec@1.11.0`"},
    "ticket": {"uses": ["plan-review", "code-review", "spin-worktree", "reviewer-memory"], "requirements": "GitHub CLI for the bundled issues binding, one binding page per other tracker; composes with `plan-review`, `code-review`, `spin-worktree`; `reviewer-memory` from this pack"},
    "ui-craft": {"uses": ["drive-local-webapp", "spin-worktree"], "requirements": "`drive-local-webapp` for rendered review; `spin-worktree` for live base comparison; parallel-agent support is recommended"},
    "ci-design": {"uses": [], "requirements": ""},
    "clean": {"uses": ["codebase-design", "domain-modeling"], "requirements": "`codebase-design` from this pack; `domain-modeling` optional"},
    "code-review": {"uses": ["reviewer-memory"], "requirements": "`reviewer-memory` from this pack; parallel-agent support recommended; GitHub CLI to fetch an originating issue; see [docs/review-round-mining.md](docs/review-round-mining.md) for the mined evidence behind the fix protocol and the round cap"},
    "codebase-design": {"uses": ["domain-modeling"], "requirements": ""},
    "domain-modeling": {"uses": ["codebase-design"], "requirements": ""},
    "drive-local-webapp": {"uses": [], "requirements": "Node.js 20+; installs Playwright locally"},
    "handoff": {"uses": [], "requirements": ""},
    "plan-review": {"uses": ["reviewer-memory"], "requirements": "`reviewer-memory` from this pack; parallel-agent support recommended; the round-count evidence behind its rules is in [docs/review-round-mining.md](docs/review-round-mining.md)"},
    "prototype": {"uses": [], "requirements": ""},
    "research": {"uses": [], "requirements": ""},
    "reviewer-memory": {"uses": [], "requirements": ""},
    "say-less": {"uses": [], "requirements": "Optional prompt hook for always-on digest; see [docs/overlay.md](docs/overlay.md) and the [measured comparison](docs/before-after.md)"},
    "spin-worktree": {"uses": [], "requirements": "Git; GitHub CLI only for `--pr` discovery"},
    "tdd": {"uses": [], "requirements": ""},
    "writing-for-agents": {"uses": [], "requirements": "Hand-only; invoke by name"},
}
