<!-- claude-opus-5 / say-less / interview round / 1549 output tokens / 6 turns -->

Found while reading: `upload()` makes 3 total calls, not the 4 the README and docstring specify — `range(config["retries"])` omits the initial attempt, and `test_gives_up_eventually` asserts `<=` so it passes either way. "Exhausts every retry" currently means one retry fewer than documented.

**Q1. Where does a permanently failed upload land?**
> A. json lines file on local disk (dead-letter log), appended per failure
> B. caller-supplied handler passed into `upload()` (dead_letter callback), storage is the caller's problem
> C. in-process list/queue object returned by the module, drained by whoever runs the batch
>
> ↳ *rec A: survives process death, which is the failure mode that makes uploads vanish; B leaves the same vanishing hole if the caller passes nothing*

**Q2. After recording the failure, what does `upload()` do?**
> A. still raises `UploadFailed` (recording is a side effect, callers unchanged)
> B. returns a sentinel result marking it dead-lettered, no exception
> C. raises only if recording the failure also fails
>
> ↳ *rec A: existing callers and `test_gives_up_eventually` keep working; "goes somewhere instead of vanishing" is satisfied by the record, not by silence*

**Q3. Does the fixed attempt count follow the README (4 calls) or today's behavior (3 calls)?**
> A. fix loop to `retries + 1`, matching README and docstring
> B. leave 3 calls, update README and docstring to match code
> C. leave the count alone, out of scope for this change
>
> ↳ *rec A: docstring states the contract explicitly, so code is the side that's wrong; one extra call per permanent failure*
