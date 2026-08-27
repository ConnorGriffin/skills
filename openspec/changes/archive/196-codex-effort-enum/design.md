# Design

`codex-worker.py` owns the local validation boundary because the Codex CLI
passes arbitrary effort values to the API. Its literal enum now reflects the
measured API set. The probe record retains the 2026-08-24 configuration-based
claim as superseded history so future changes can distinguish it from the live
2026-08-27 result.
