# Planning and review routing — deltas

## ADDED Requirements

### Requirement: Research worker source access

A research-worker dispatch MUST explicitly enable provider-hosted web search
and fetch while preserving the selected filesystem sandbox, and the selected
adapter MUST persist that capability across resume. The capability MUST remain
off for dispatches that do not request it and MUST NOT promise arbitrary shell
network access.

When the provider refuses or cannot supply hosted source access, the
coordinator MUST fetch the required primary sources into session scratch and
resume the same worker against the local material. If neither path can obtain
the required sources, the research workflow MUST stop clearly and MUST NOT
report completed research or write a successful findings artifact.

#### Scenario: Research starts with hosted source access

- **WHEN** the research skill dispatches a read-only worker
- **THEN** the selected adapter enables its hosted web tools without granting
  repository writes or arbitrary command-network access

#### Scenario: Research resumes after provider refusal

- **WHEN** a hosted web tool is denied or unavailable
- **THEN** the coordinator places fetched primary-source material in session
  scratch and resumes the same worker against that material

#### Scenario: A non-research worker starts normally

- **WHEN** an adapter start omits the hosted-web opt-in
- **THEN** hosted live source access remains disabled and the existing sandbox
  behavior is unchanged

