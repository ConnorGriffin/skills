import unittest

from uploader import CONFIG, UploadFailed, upload


class FlakyClient:
    def __init__(self, fail_times):
        self.fail_times = fail_times
        self.calls = 0

    def put(self, artifact):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("connection reset")
        return {"artifact": artifact, "attempts": self.calls}


class RetryTest(unittest.TestCase):
    def test_succeeds_after_transient_failures(self):
        client = FlakyClient(fail_times=2)
        result = upload(client, "build.tar.gz", {"retries": 3, "backoff_seconds": 0})
        self.assertEqual(result["attempts"], 3)

    def test_gives_up_eventually(self):
        client = FlakyClient(fail_times=99)
        with self.assertRaises(UploadFailed):
            upload(client, "build.tar.gz", {"retries": 3, "backoff_seconds": 0})
        self.assertLessEqual(client.calls, CONFIG["retries"] + 1)


if __name__ == "__main__":
    unittest.main()
