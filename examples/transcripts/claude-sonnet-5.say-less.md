<!-- claude-sonnet-5 / say-less / 636 output tokens / 6 turns -->

`upload()`'s loop runs `range(config["retries"])` — 3 calls total, not the 4 (1 + 3 retries) the README/config contract promises; fix is `range(config["retries"] + 1)`. Tests stay green because `test_gives_up_eventually` only asserts `calls <= retries + 1` (passes at 3) and the success test uses `fail_times=2` so it never exercises the 4th call — neither test pins down the exact count Ops needs.
