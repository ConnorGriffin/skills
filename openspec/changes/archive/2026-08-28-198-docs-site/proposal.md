# Documentation site

## Why

People evaluating the pack need an overview of skills, workflows, and their
relationships without opening every source file.

## What changes

- Add a standard-library static-site generator sourced from SKILL.md files.
- Add hand-maintained relationship data and workflow narratives.
- Publish the generated site through GitHub Pages after validation.

## Risk contract

The generator validates that every skill and relationship endpoint exists, so it
does not silently publish a page for a missing skill. It has no network access,
runtime JavaScript, secrets, or third-party dependencies. Narrative and edge
semantic staleness remains a visible maintenance responsibility.
