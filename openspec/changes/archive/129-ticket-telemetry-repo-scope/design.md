# Design

Claims already carry the repository resolved from their project at claim time.
The smallest interface is therefore the existing `--project` value on `scan`
and `record`: it resolves the repository used to select claims, while leaving
the current directory as the default for established invocations.

`unmeasurable` is reserved for a claim set belonging to the selected repository
that cannot yield the peak required for a sizing call. No-claim and wrong-repo
paths remain `no-data`. A chunked ticket with coordinator or reviewer context
but no worker peak remains `coordinator-only`, as its existing contract already
states that the work was measured but chunk size was not.
