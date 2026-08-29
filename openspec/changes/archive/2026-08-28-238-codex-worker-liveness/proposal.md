# Wait before diagnosing a quiet Codex worker

## Why

The Codex adapter buffers output while its child is active. A coordinator can therefore
mistake an ordinary quiet interval for a hang.

## What changes

- Tell coordinators to wait another minute when a Codex adapter is still running but
  quiet.
- State that silence or an empty session ID alone is not evidence of a hang.
- Pin the instruction in a behavior test because agent-facing prose is executable
  workflow policy.

No worker lifecycle or adapter code changes.
