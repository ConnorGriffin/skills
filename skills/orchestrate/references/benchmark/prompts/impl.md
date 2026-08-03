Area: hermetic implementation. Working copy: an isolated git worktree (one per model) of the target app pinned to the pre-fix commit recorded in ../README.md. Backend tests: `python3 -m unittest discover -s tests`; frontend tests: `node --test frontend/`.
At replay time, insert the full issue body below this line (fetch with `gh issue view <N> -R <owner/repo>` from the source repo — it is private; never commit the body to this public pack):

<ISSUE BODY HERE>

Implement a fix for the issue in your worktree, with tests that exercise the new behavior through the public interface. Run both test suites and report actual output (record the baseline failure count first — pre-existing environment errors are not yours). Do not commit. Finish with a summary: files changed, behavior change, test evidence.
