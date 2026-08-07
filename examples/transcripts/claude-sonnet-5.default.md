<!-- claude-sonnet-5 / default / 2005 output tokens / 6 turns -->

I don't have write permission here yet, so here's the fix for you to apply (or approve the edit):

**`uploader.py` line 18** — change:
```python
for attempt in range(config["retries"]):
```
to:
```python
for attempt in range(config["retries"] + 1):
```
This gives 1 initial attempt + `retries` retries, matching the README/docstring contract.

**`test_uploader.py`** should also be tightened so it actually catches this class of bug:
- `test_succeeds_after_transient_failures`: use `fail_times=3` (needs all 4 calls, i.e. success only on the last retry) instead of `fail_times=2`, so the test fails if the retry budget is short.
- `test_gives_up_eventually`: assert `client.calls == CONFIG["retries"] + 1` (exact count) instead of `<=`, so an early giveup is caught rather than allowed as "within bounds."

Want me to apply these three edits?
