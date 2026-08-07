<!-- claude-fable-5 / say-less / 840 output tokens / 4 turns -->

Off-by-one in `uploader.py:18`: `range(config["retries"])` makes 3 total attempts instead of 1 + 3 retries — change to `range(config["retries"] + 1)`. Tests stay green because `test_gives_up_eventually` asserts `calls <= retries + 1` instead of `== retries + 1` (test_uploader.py:28) — tighten it to `assertEqual(client.calls, 4)`.
