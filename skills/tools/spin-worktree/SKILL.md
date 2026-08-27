---
name: spin-worktree
description: Create an isolated Git worktree for issue, pull-request, branch, or parallel agent work without editing the control checkout. Use when starting task work from fresh remote state, avoiding a dirty or shared checkout, or preparing a dedicated worktree for another agent.
---

# Spin an isolated worktree

Keep the ordinary checkout as the control checkout and create one worktree per
task. Dirty files in the control checkout are preserved and do not block the
helper: it updates Git refs and shared worktree metadata, creates the destination,
and never switches, stashes, or edits files in the control checkout.

By default worktrees live under `${AGENT_WORKTREE_ROOT:-~/worktrees}`:

```text
~/worktrees/<repository>/<task>
```

## Workflow

1. Resolve the ordinary checkout and pass it explicitly with `--repo`. Never
   substitute another task's linked worktree just because it is clean. If a
   linked worktree is passed accidentally, the helper resolves Git's primary
   worktree before deriving `<repository>` or running commands.
2. Resolve this installed skill's directory.
3. Run one of the commands below.
4. Report the exact path and use it as the working directory.
5. Do not remove the worktree automatically. Cleanup belongs to task closeout
   after merge.

New issue branch:

```sh
python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
  --repo /path/to/repository \
  --issue 317 \
  --slug rescue-context
```

Existing pull-request branch, discovered with GitHub CLI:

```sh
python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
  --repo /path/to/repository \
  --pr 321
```

Existing branch:

```sh
python3 <spin-worktree-skill-directory>/scripts/spin-worktree.py \
  --repo /path/to/repository \
  --branch issue-316 \
  --name pr321
```

Use `--dry-run` to inspect commands. Override defaults with
`--worktree-root`, `--remote`, `--base`, or `--branch-prefix`.

## Branch prefix

New issue branches resolve their prefix in this order: an explicitly supplied
`--branch-prefix` flag, then the string `branchPrefix` in
`~/.config/spin-worktree/config.json`, then no prefix. For example:

```json
{"branchPrefix": "my-prefix"}
```

With no resolved prefix, issue branches are `issue-317` or
`317-rescue-context`; they never begin with `/`. Pass `--branch-prefix ''` to
request that bare form for one invocation. Missing, unreadable, malformed, or
otherwise unsuitable config files silently resolve to no prefix.

## Guardrails

- Use one worktree path and branch per task.
- Never switch branches in another agent's active worktree.
- Do not reuse an existing target path unless inspection proves it belongs to
  the same task.
- New issue work updates the remote and starts from its current default branch
  unless `--base` is supplied.
- Existing local branches do not require a remote.
- Pull-request discovery requires authenticated `gh`. A same-repository head
  is fetched when needed. A fork head fails with the exact fork and branch to
  configure, rather than pretending it exists under `origin`.
- `--name` accepts one relative directory leaf, never a path.
