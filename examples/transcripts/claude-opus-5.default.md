<!-- claude-opus-5 / default / 2189 output tokens / 7 turns -->

Ops is right; the code is off by one.

**The bug** — `uploader.py:18`:

```python
for attempt in range(config["retries"]):   # 3 iterations = 3 total calls
```

`retries=3` yields 3 attempts total, not 1 + 3 = 4. Confirmed: a client that always fails gets exactly 3 `put` calls. The docstring at `uploader.py:3-4` and README both promise 4, so the code — not the config or docs — is what's wrong.

**Why the suite stayed green** — neither test can see the difference:

- `test_succeeds_after_transient_failures` uses `fail_times=2`, so it succeeds on call 3. Passes under both 3-call and 4-call behavior.
- `test_gives_up_eventually` asserts `client.calls <= CONFIG["retries"] + 1` — `3 <= 4` passes. The `<=` makes the assertion satisfiable by any under-count, which is exactly the failure mode in play.

**What should change**

1. `uploader.py:18` → `for attempt in range(config["retries"] + 1):`
2. `test_uploader.py:28` → `assertEqual(client.calls, 4)`. An exact count is the whole point of this test; `<=` cannot fail in the direction that matters.
3. Add a boundary test at `fail_times=3` — succeeds on the 4th call under the fixed code, raises under the current code. That's the case neither existing test covers.

One thing to decide while you're in there: the `time.sleep` at line 23 runs after the final failed attempt too, so a give-up burns a full 2s backoff before raising. Worth skipping the sleep on the last iteration.

Want me to apply these?
