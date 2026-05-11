---
name: flywheel-weekly-memory-consolidation
description: |
  Weekly batch job that reads recent project artifacts, summarizes durable lessons,
  and writes them to Gbrain. STUB - implementation deferred to Phase 13.
status: stub
priority: medium
---

# Phase 13 work: Weekly Memory Consolidation

## Intent

- Read recent project artifacts: last 7 days of PR summaries, closed beads, and
  CURRENT_STATE.md updates
- Synthesize durable lessons: what worked, what failed, what pattern emerged
- Append to Gbrain under `retrospectives/<date>-<project>.md` or
  `projects/<project>/retrospectives/<date>.md` after the schema is finalized
- Trigger Gbrain import/search refresh for the new retrospective

## Acceptance criteria to satisfy when actually implemented

- Runs weekly via cron or Hermes cronjob
- Outputs a single markdown file per project per week
- Filtered through `policies/GBRAIN_POLICY.md`
- Never writes anything in the deny list
- Idempotent and safe to re-run
- Includes a dry-run mode that prints what would be written without changing the
  brain repo or Gbrain database
- Updates the project's CURRENT_STATE.md with the consolidation result

## NOT in scope for the skill

- Real-time ingestion; this is batch, not continuous
- Cross-project synthesis; separate skill
- Personal context ingestion; forbidden by current policy
- Dream cycle automation; deferred until Gbrain behavior is observed on the safe
  corpus

## Implementation notes

This skill is a Flywheel skill like skills 1-4. Build it in Phase 13 after
observing actual Gbrain usage and deciding what a "durable lesson" should look
like in practice.

The skill must read, in order:

1. `policies/GBRAIN_POLICY.md`
2. `runbooks/backup-restore-gbrain.md`
3. `runbooks/delete-gbrain-memory.md`
4. The target project's CURRENT_STATE.md
5. The last 7 days of merged PR summaries and closed bead reports

Hard gate: if any candidate content matches the deny list in GBRAIN_POLICY.md,
the skill must stop and surface the content path to the user instead of writing
to the brain.
