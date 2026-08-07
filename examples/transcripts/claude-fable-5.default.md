<!-- claude-fable-5 / default / 1360 output tokens / 5 turns -->

The code implements retries as *total attempts*, while the README, the docstring, and ops' expectation all define `retries` as attempts *after* the first one. In `uploader.py:18`, `for attempt in range(config["retries"])` makes exactly 3 calls with `retries: 3`, so the upload gives up after 3 tries instead of the promised 4. The config value and the README are consistent with each other — the loop is the bug.

The test suite stays green because it never pins down the off-by-one:

- `test_succeeds_after_transient_failures` uses a client that fails only twice, so 3 total attempts is enough to pass under either interpretation.
- `test_gives_up_eventually` asserts `client.calls <= CONFIG["retries"] + 1` — a one-sided bound that 3 calls satisfies just as well as 4. It would only catch making *too many* attempts, not too few.

What should change:

1. **`uploader.py:18`** — loop over `range(config["retries"] + 1)` so `retries: 3` yields one initial attempt plus 3 retries.
2. **`test_uploader.py:28`** — replace the `assertLessEqual` with `assertEqual(client.calls, CONFIG["retries"] + 1)` so the contract is actually pinned; the success test could also use a `fail_times=3` case that succeeds on the 4th call, which fails today and locks in the fix.
3. Optionally, skip the `time.sleep` after the final failed attempt in `uploader.py:23` — right now the code backs off before raising `UploadFailed`, which delays the failure for no benefit (with the default config that's a pointless 2-second wait at the end).

Since you asked what's wrong rather than for a fix, I've left the code untouched — happy to apply these changes if you want.
