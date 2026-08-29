# Planning and review routing — deltas

## ADDED Requirements

### Requirement: Research worker source access

A research-worker dispatch MUST explicitly enable provider-hosted web search
and fetch while preserving the selected filesystem sandbox, and the selected
adapter MUST persist that capability across resume. The capability MUST remain
off for dispatches that do not request it and MUST NOT promise arbitrary shell
network access.

When a successfully completed, resumable worker reports hosted source refusal
with the defined worker result, the coordinator MUST fetch the required public
primary sources into a unique scratch directory under the worker cwd and resume
the same worker against a manifest of that local material. This handoff is the
sole exception to the original-prompt-only worker-input rule. If the adapter
fails without a resumable session, or neither source path can obtain the
required sources, the research workflow MUST stop clearly and MUST NOT report
completed research or write a successful findings artifact.

#### Scenario: Research starts with hosted source access

- **WHEN** the research skill dispatches a read-only worker
- **THEN** the selected adapter enables its hosted web tools without granting
  repository writes or arbitrary command-network access

#### Scenario: Research resumes after provider refusal

- **WHEN** a successfully completed worker reports hosted web refusal as
  `SOURCE_ACCESS_UNAVAILABLE:` and its state is resumable
- **THEN** the coordinator places only public fetched sources and their URL
  manifest in a unique cwd-local scratch directory and resumes that same worker
  with the manifest path

#### Scenario: The failed worker cannot resume

- **WHEN** an adapter failure leaves no terminal state with a session ID
- **THEN** research stops visibly and writes no successful findings artifact

#### Scenario: A non-research worker starts normally

- **WHEN** an adapter start omits the hosted-web opt-in
- **THEN** hosted live source access remains disabled and the existing sandbox
  behavior is unchanged
