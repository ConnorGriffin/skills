## REMOVED Requirements

### Requirement: Scope routing

**Reason**: ADR 300 deletes the `scope` skill. Resolving open decisions before a
work order locks belongs to ticket triage.

**Migration**: Use `/ticket triage`. The ticket rewrite under issue 300 specifies
how triage resolves open decisions.

### Requirement: Scope records and risk admission

**Reason**: ADR 300 deletes the `scope` skill that owned scope ledgers and risk
admission.

**Migration**: Use `/ticket triage`. The ticket rewrite under issue 300 specifies
where the settled risk contract is recorded.

### Requirement: Patient Codex worker liveness checks

**Reason**: ADR 300 removes `orchestrate` and its Codex worker adapter, so there
is no pack-owned adapter whose liveness the coordinator polls.

**Migration**: Dispatch Codex work through the codex plugin (`/codex:rescue`,
`/codex:review`) or ask Codex directly.

### Requirement: Write-mode workers retain a durable closed order

**Reason**: ADR 300 removes `orchestrate`, the canonical home of the durable-order
rule and its adapter dispatch.

**Migration**: Write-mode work runs as native subagents with worktree isolation.
The ticket rewrite under issue 300 specifies any order-file rule chunked tickets
keep.

### Requirement: Orchestration isolation and review handoff

**Reason**: ADR 300 supersedes ADR 149 and ADR 150; dispatch no longer goes
through pack-owned isolated adapters.

**Migration**: Follow `profile/base.md` "Delegating to subagents". The ticket
workflow's `Coordinator-owned review handoff` requirement still governs
mandatory review reached by delegated ticket work.

## MODIFIED Requirements

### Requirement: Review routing and containment

`/review` MUST classify a review subject and route it to exactly one registered
review skill. A registered route whose implementation is missing MUST stop rather
than substitute another review.

#### Scenario: A registered review route is unavailable

- **WHEN** route resolution finds the requested route but cannot find its named
  review skill
- **THEN** review stops with the missing-skill result and does not run a nearby
  route

### Requirement: Research worker source access

A research-worker dispatch MUST run one read-only subagent with hosted web search
and fetch allowed and MUST NOT grant repository writes or promise arbitrary shell
network access.

When a completed, resumable worker reports hosted source refusal with the defined
worker result, the coordinator MUST fetch the required public primary sources into
a unique scratch directory under the worker cwd and resume the same worker against
a manifest of that local material. This handoff is the sole exception to the
original-prompt-only worker-input rule. If the worker leaves no resumable session,
or neither source path can obtain the required sources, the research workflow MUST
stop clearly and MUST NOT report completed research or write a successful findings
artifact.

#### Scenario: Research starts with hosted source access

- **WHEN** the research skill dispatches its worker
- **THEN** the worker is a read-only subagent with hosted web tools allowed and no
  repository writes

#### Scenario: Research resumes after provider refusal

- **WHEN** a completed worker reports hosted web refusal as
  `SOURCE_ACCESS_UNAVAILABLE:` and its session is resumable
- **THEN** the coordinator places only public fetched sources and their URL
  manifest in a unique cwd-local scratch directory and resumes that same worker
  with the manifest path

#### Scenario: The failed worker cannot resume

- **WHEN** the worker fails and leaves no resumable session
- **THEN** research stops visibly and writes no successful findings artifact

#### Scenario: A non-research worker starts normally

- **WHEN** a subagent is dispatched without hosted web tools in its allowlist
- **THEN** hosted live source access remains disabled and its other tools are
  unchanged
