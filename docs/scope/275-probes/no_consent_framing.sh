#!/bin/sh
# Ticket 275 probe: no worker-egress consent framing survives in the shipped pack.
#
# Scope is the two skills that carried the grant plus the scripts that generated it.
# The ui-craft hits for "consent" are git-hook install consent and are out of scope;
# docs/scope/, docs/adr/, and openspec/changes/archive/ are historical record and are
# deliberately not searched.
#
# Exit 0 when nothing matches. Exit 1 and print every surviving line otherwise.
set -eu
cd "$(git rev-parse --show-toplevel)"

# Keyword terms plus the phrases that carry the framing with no keyword in them:
# a wrapped exclusions sentence and the adapter escalation rationale.
PATTERN='consent|worker-egress|bounded transfer|already granted this dispatch|model service'
PATTERN="$PATTERN|real database contents|exclusion list|escalation justification|user authorization"

hits=$(grep -rniE "$PATTERN" \
  skills/drivers/ticket skills/drivers/orchestrate scripts \
  | grep -viE 'regression' || true)

if [ -n "$hits" ]; then
  printf '%s\n' "$hits"
  printf 'FAIL: %s surviving consent-framing lines\n' "$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
  exit 1
fi

printf 'OK: no consent framing in skills/drivers/ticket, skills/drivers/orchestrate, scripts\n'
