# BR-017 — Evolving "One Thing to Not Do" From Feedback

Status: implemented as a conservative, recommend-only evolution path.
Related MT PR review follow-up: BR-017 was created after MT flagged that the
"One Thing to Not Do" job should not remain a static prompt. Its role is to be a
small diagnostic anti-priority that adapts to James/MT's recurring operating
failure modes without becoming coaching, blame, or a reprimand.

## Intended role

"One Thing to Not Do" is a daily guardrail, not a motivational message. It should
name the single avoidable failure mode most likely to distort the day's work and
turn it into a concrete negative checkpoint. Good output is short, specific, and
operational:

- Diagnostic: names the pattern, e.g. architecture-as-avoidance or scope creep.
- Specific: points at the current execution risk, not a generic personality flaw.
- Non-scolding: says "Do not expand today's accepted slice..." rather than "You
  always overcomplicate things."
- Recommend-only: it never mutates Kanban and does not write Gbrain during daily
  delivery.

## Feedback sources

The update loop uses derived signals from three sources. The script accepts these
as normalized feedback state through `--feedback-json`; runtime collectors may
produce that state from the sources below.

1. Gbrain
   - Read `guardrails/anti-patterns` for durable named patterns.
   - Read `guardrails/diagnostic-observations` for dated, distilled observations.
   - Treat Gbrain as the highest-signal source because it is already curated for
     30-day durability.

2. Kanban
   - Read recent run summaries, blocked reasons, retry outcomes, review-gate
     failures, and oversized-task/cleanup findings from roughly the last 7 days.
   - Extract pattern language, not task-log detail. "Review gate drift recurred"
     is useful; "task t_x failed at 18:43" belongs in Kanban, not Gbrain.

3. Session-derived feedback
   - Use explicit MT feedback and assistant session summaries when they identify
     a repeated operating pattern.
   - Session feedback is lower-confidence unless corroborated by Kanban or
     Gbrain, because a single conversation can reflect the day's mood rather than
     a durable pattern.

## Recurrence threshold and noise guard

The daily recommendation may switch away from the deterministic fallback only
when one of these is true:

- Corroborated pattern: at least two matching signals from at least two source
  classes, for example Gbrain + Kanban or Kanban + session.
- Recurring pattern: at least three matching signals across at least two dates.

A single session comment, one blocked task, or one noisy day is not enough. If no
pattern clears the threshold, `no_do.py` returns the deterministic fallback:

"Do not turn today's task into a new architecture, broader scope, or fresh
abstraction; finish the smallest accepted slice."

This makes the mechanism adaptive while preserving hysteresis: new evidence can
move the recommendation, but daily noise cannot whip it around.

## Language contract

Every recommendation must satisfy all of the following:

- Label remains exactly `One Thing to Not Do Today`.
- Maximum two sentences.
- Starts from the task/workflow behavior to avoid, not from MT's character.
- Contains a concrete operational checkpoint: accepted slice, named deliverable,
  verified checkpoint, CI/review gate, or PR/task closure.
- Avoids scolding language such as "always," "never learn," "failure," "lazy,"
  or blame-directed phrasing.

Examples:

- Good: "Do not expand today's accepted slice into adjacent improvements; ship or
  review the smallest named deliverable before adding another bead."
- Good: "Do not count the work as complete until the real gate is cleared; verify
  CI, formal review, or MT approval before moving to the next item."
- Bad: "Stop overcomplicating things again."

## Write-back boundaries: Gbrain vs persistent memory

Gbrain is the right destination for durable, project-relevant operating patterns:

- Named anti-patterns under `guardrails/anti-patterns`.
- Dated distilled observations under `guardrails/diagnostic-observations`.
- Stable pattern evidence summarized without raw logs, secrets, or ephemeral task
  IDs as durable prose.

Daily delivery does not write to Gbrain. A future collector or consolidation task
may propose/write a guardrail only when it meets the recurrence threshold, is not
a near-duplicate of an existing guardrail, and respects the one-write-per-week
freshness rule in `GBRAIN_CONVENTIONS.md`.

Persistent Hermes memory is narrower. Use it only for stable user-level facts or
preferences that should be injected into future sessions, such as "MT prefers
non-scolding diagnostic language for no-do guardrails." Do not store daily no-do
outputs, Kanban run outcomes, raw feedback excerpts, or evolving guardrail
candidate state in persistent memory; those belong in Kanban/session history or
Gbrain after consolidation.

## Implementation notes

- `morning-briefing/scripts/no_do.py` now contains the failure-mode catalog,
  recurrence scoring, and optional `--feedback-json` input.
- `morning-briefing/tests/test_no_do.py` verifies deterministic fallback,
  adaptive selection from corroborated feedback, and the no-overfitting guard for
  a single session signal.
- `morning-briefing/config/jobs.yaml` keeps daily delivery recommend-only and
  disallows Gbrain writes on delivery while documenting the 7-day read window.
