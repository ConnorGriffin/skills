# Design

`None` represents an omitted `--branch-prefix` flag, preserving an explicitly
supplied empty string as an instruction to create a bare branch. The helper
reads its single optional JSON file at the durable-input boundary and treats
every unavailable or unsuitable value as no prefix.
