# uploader fixture

Uploads a build artifact through a client that occasionally drops the connection.

`retries` in `CONFIG` is the number of retries *after* the first attempt: with
`retries: 3` an upload gets one initial attempt plus 3 retries, 4 calls in total,
with exponential backoff between them.

Run the tests: `python3 -m unittest discover -s . -q`
