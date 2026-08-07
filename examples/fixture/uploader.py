"""Artifact uploader with retry.

Config contract (see README): `retries` is the number of retries *after* the
first attempt, so retries=3 means up to 4 total calls.
"""

import time

CONFIG = {"retries": 3, "backoff_seconds": 0.5}


class UploadFailed(Exception):
    pass


def upload(client, artifact, config=CONFIG):
    last_error = None
    for attempt in range(config["retries"]):
        try:
            return client.put(artifact)
        except Exception as exc:
            last_error = exc
            time.sleep(config["backoff_seconds"] * (2 ** attempt))
    raise UploadFailed(f"upload of {artifact} failed: {last_error}")
