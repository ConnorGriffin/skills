<!-- claude-opus-5 / say-less / 848 output tokens / 5 turns -->

Wrong: `uploader.py:18` loops `range(retries)` = 3 total calls, so the README's 4 (1 initial + 3 retries) never happens; config and README are correct. Change the loop to `range(config["retries"] + 1)`, skip the sleep after the last attempt, and tighten `test_uploader.py:28` from `assertLessEqual` to `assertEqual(client.calls, 4)` — the loose bound is why the suite stayed green.
