# Truthful full-gate worker completion reports

## Why

Worker completion reports have sometimes represented focused, bypassed, failed, or
interrupted verification as the full verification requested in the brief. The
coordinator already independently verifies delegated results before shipping; this
change makes the worker's evidence boundary explicit.

## What changes

Require workers to name and paste the complete output of the brief's exact successful
verification command before claiming it passed. Label partial checks as supplemental,
disclose bypasses, and report incomplete commands as unverified.

## Risk contract

- **Must prevent:** a completion report representing a partial, bypassed, failed, or
  interrupted check as the brief's full successful verification.
- **Must recover:** workers report the verification as incomplete; the coordinator's
  existing independent verification decides whether the result can ship.
- **Accepted failure:** an agent may still misread the prose, costing a rerun.
- **Unsupported:** parsing, validation, provenance capture, or runtime enforcement.
- **Evidence owed:** the one prose pin and the repository gate.
