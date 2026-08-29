# Generated facts: issue 265 OpenSpec applicability

Every block below is verbatim output from the named command in the issue 265
worktree. Regenerate this file after changing the cited probe, OpenSpec change, or
verification runtime.

## Historical regression

Command:

```sh
/opt/homebrew/bin/python3.14 docs/scope/265-probes/reproduce_259.py
```

Output:

```text
$ openspec --version
1.11.0
exit=0
$ openspec validate 259-remove-unused-ticket-telemetry --strict
Change '259-remove-unused-ticket-telemetry' is valid
exit=0
$ /opt/homebrew/opt/python@3.14/bin/python3.14 docs/scope/265-probes/preflight_openspec.py 259-remove-unused-ticket-telemetry --repo .
ticket: ticket-workflow MODIFIED failed for header "### Requirement: Role-aware measurement and review depth" - not found
ticket: if this requirement was renamed, add a `## RENAMED Requirements` mapping from its current baseline header to the unmatched delta header; otherwise correct the MODIFIED header.
exit=1
source_unchanged=true
```

## Archive command surface

Command:

```sh
openspec archive --help
```

Output:

```text
Usage: openspec archive [options] [change-name]

Archive a completed change and update main specs

Options:
  -y, --yes      Skip confirmation prompts
  --skip-specs   Skip spec update operations (useful for infrastructure,
                 tooling, or doc-only changes)
  --no-validate  Skip validation (not recommended, requires confirmation)
  --json         Output as JSON (non-interactive)
  --store <id>   Store id to use as the OpenSpec root (a store is a standalone
                 OpenSpec repo you've registered)
  -h, --help     display help for command
```

## Changed active-change discovery

Command:

```sh
/opt/homebrew/bin/python3.14 docs/scope/265-probes/discover_changed_openspec.py --repo . --base-ref refs/remotes/origin/HEAD
```

Output:

```text
265-preflight-openspec-rename-applicability
```

## Current OpenSpec validation

Command:

```sh
openspec validate --all --strict
```

Output:

```text
- Validating...
✓ change/265-preflight-openspec-rename-applicability
✓ spec/pack-integrity
✓ spec/planning-and-review
✓ spec/ticket-workflow
Totals: 4 passed, 0 failed (4 items)
```

## Host Python runtimes

Command:

```sh
/opt/homebrew/bin/python3.14 --version
```

Output:

```text
Python 3.14.7
```

Command:

```sh
python3 --version
```

Output:

```text
Python 3.9.6
```
