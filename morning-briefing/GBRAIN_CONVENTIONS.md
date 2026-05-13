# GBRAIN_CONVENTIONS.md — Morning Briefing System

**Status:** Approved for implementation
**Timezone:** America/New_York throughout
**Author:** James Lafarge (kanban task t_55b1338b)
**Last updated:** 2026-05-13

---

## Overview

This document defines how the Morning Briefing System interacts with Gbrain.
It specifies the four canonical page/concept namespaces, what each cron job is
allowed to read and write, and what is permanently prohibited from Gbrain storage.

Gbrain is MT's long-term memory and research reference — not a task log.
The governing principle: **write only what will matter in 30 days; never write
what happened today for the sake of completeness.**

---

## 1. Gbrain Stack Reference

- Engine: local PostgreSQL 18 + pgvector (DB: `gbrain`)
- Config: `~/.gbrain/config.json`
- Connection URL: `~/.gbrain/database_url` (mode 600, never committed)
- CLI: `gbrain` (must be on PATH in cron job environment)
- Python access: `gbrain` Python library (reads `~/.gbrain/config.json`)
- Vector search: `gbrain search "<query>"` or Python client `.search()`
- Page write: `gbrain write "<title>" "<body>"` or Python client `.write()`

Policy dependency: these conventions assume the Phase 12 PostgreSQL + pgvector
Gbrain policy/runbook has landed on `main`. If the repo still documents the
legacy `~/.gbrain/brain.pglite` boundary, morning jobs must run in read-only
mode and defer all writes until the Gbrain policy is updated and explicitly
approved.

---

## 2. Canonical Page Namespaces

The Morning Briefing System owns four Gbrain page namespaces.
All pages created by morning jobs must fall inside one of these namespaces.
Pages outside these namespaces must not be created or modified by morning jobs.

### 2.1 Morning Briefing System

**Namespace prefix:** `morning-system/`

Purpose: operational configuration and system-level notes that span all jobs.
Not a run log. Contains stable facts that implementers and future agents need.

Pages:

| Page title | Written by | Purpose |
|---|---|---|
| `morning-system/watchlist` | Manual / kanban task | Master company list with ticker, sector, coverage tiers. Single authoritative source; never auto-overwritten. |
| `morning-system/domain-list` | Manual / kanban task | MT's interest domains for analogy + idea generation. Stable; only MT edits. |
| `morning-system/job-registry` | Manual / kanban task | Maps job name → cron ID → output contract. Implementation reference. |

Rules:
- Morning jobs read from this namespace but do not write to it.
- Changes go through PR review, not agent writes.
- These pages serve as **system state**, not session state.

### 2.2 Watchlist Research Rubric

**Namespace prefix:** `watchlist/`

Purpose: per-company research notes, materiality judgments, and coverage history.
This is what the Watchlist Digest job reads before deciding whether to surface an item.

Pages:

| Page title pattern | Written by | Purpose |
|---|---|---|
| `watchlist/<TICKER>` | `company_watchlist` job | Last-surfaced date, recent material items, coverage notes. One page per company. |
| `watchlist/<TICKER>/rubric` | Manual / kanban task | Company-specific materiality filter: what counts as material for this name, what to ignore. |

Fields written to `watchlist/<TICKER>` by the job:

```
last_surfaced: YYYY-MM-DD
items:
  - date: YYYY-MM-DD
    headline: "<text>"
    source_tier: 1|2|3|4
    materiality: high|medium|low
    note: "<1-sentence context>"
```

Retention: a job must not write more than 10 items per company page.
Trim the oldest when the 11th would be added.

Rules:
- The `company_watchlist` job reads `watchlist/<TICKER>` to check recency before surfacing an item.
- The `company_watchlist` job writes `watchlist/<TICKER>` after delivering a material item.
- An item that was surfaced in the last 3 days must not be surfaced again unless materiality has increased.
- The `investment_question` job reads `watchlist/<TICKER>` for active threads.
- No other morning jobs write to `watchlist/` pages.

### 2.3 Idea History / Creative Constraints

**Namespace prefix:** `ideas/`

Purpose: record of delivered overnight ideas and cross-domain analogy seeds,
so future runs can avoid repetition and build on prior creative threads.

Pages:

| Page title pattern | Written by | Purpose |
|---|---|---|
| `ideas/overnight/<YYYY-MM-DD>` | `overnight_ideas` job | One page per delivery. All 12 ideas (4 buckets × 3) in structured form. |
| `ideas/analogy/<YYYY-MM-DD>` | `cross_domain_analogy` job | The essay seed delivered that day. |
| `ideas/constraints` | Manual / kanban task | MT's standing creative constraints: domains to exhaust, pairings to avoid, recurring ruts. |

Fields written to `ideas/overnight/<YYYY-MM-DD>`:

```
date: YYYY-MM-DD
buckets:
  kanban_good_to_great:
    - idea: "<text>"
      seed_tags: [tag1, tag2]
  extend_mt_capabilities:
    - ...
  coding_stack_efficacy:
    - ...
  new_project_ideas:
    - ...
```

Fields written to `ideas/analogy/<YYYY-MM-DD>`:

```
date: YYYY-MM-DD
domains: [domain_a, domain_b]
seed: "<essay seed text>"
```

Rules:
- `overnight_ideas` reads `ideas/overnight/` (last 7 days) to avoid repeating ideas verbatim.
- `overnight_ideas` reads `ideas/constraints` for standing exclusions.
- `cross_domain_analogy` reads `ideas/analogy/` (last 30 days) to avoid re-using the same domain pair.
- `cross_domain_analogy` reads `ideas/constraints` for domain pairing rules.
- Both jobs write their output page after delivery, not before.
- Neither job writes to `ideas/constraints` — only MT or a designated kanban task may edit that page.

### 2.4 MT Operating Guardrails

**Namespace prefix:** `guardrails/`

Purpose: durable anti-patterns, scope-creep signals, and diagnostic observations
drawn from Kanban run history, session-derived feedback, and MT's operating
patterns. The `no_do` job reads from here to generate its daily
one-thing-not-to-do: a diagnostic anti-priority, not coaching or scolding. See
`BR-017_NO_DO_FEEDBACK.md` for the full BR-017 feedback-loop contract.

Pages:

| Page title pattern | Written by | Purpose |
|---|---|---|
| `guardrails/anti-patterns` | Manual + consolidation task / `no_do` write mode (rare) | Named anti-patterns with description and historical signal. |
| `guardrails/scope-creep-log` | Manual / kanban task | Documented instances of scope creep, with stable project references and resolution. |
| `guardrails/diagnostic-observations` | Manual + consolidation task / `no_do` write mode (rare) | One-liner observations about MT's work patterns, dated. |

Fields in `guardrails/anti-patterns` entries:

```
- name: "<pattern name>"
  description: "<2-3 sentences>"
  signals: [kanban-pattern, session-feedback, gbrain-observation]
  first_observed: YYYY-MM-DD
  last_triggered: YYYY-MM-DD
```

Rules:
- `no_do` reads `guardrails/anti-patterns` and `guardrails/diagnostic-observations` every run.
- `no_do` reads Kanban run history (last 7 days) directly from the board — it does not
  write Kanban state to Gbrain.
- `no_do` may consume session-derived feedback only after it has been distilled into
  a compact signal. Raw transcripts, chain-of-thought, and daily task logs are never
  written into Gbrain.
- A daily `no_do` delivery does **not** write to Gbrain. A future collector,
  consolidation task, or explicit write mode may write to `guardrails/anti-patterns`
  only when it identifies a new pattern that has either (a) at least two matching
  source classes or (b) at least three matching signals across at least two dates,
  and has no existing matching entry. Write threshold is conservative: if unsure,
  don't write.
- `no_do` must not write more than one new guardrail entry per calendar week.
- Human-authored entries in `guardrails/` take precedence; the job must not overwrite them.
- Persistent Hermes memory is only for stable user preferences/facts. Do not store
  daily `no_do` outputs, Kanban run outcomes, or guardrail candidate state there;
  use Gbrain after consolidation or local run state instead.

---

## 3. Read / Write Matrix

```
Job                    | Reads                                  | Writes
-----------------------|----------------------------------------|----------------------------------
dc_weather             | (none)                                 | (none)
company_watchlist      | watchlist/<TICKER>                     | watchlist/<TICKER>
kanban_morning_brief   | (none — reads Kanban directly)         | (none)
kanban_cleanup_proposal| (none — reads Kanban directly)         | (none)
overnight_ideas        | ideas/overnight/ (last 7 days)         | ideas/overnight/<YYYY-MM-DD>
                       | ideas/constraints                      |
                       | morning-system/domain-list             |
cross_domain_analogy   | ideas/analogy/ (last 30 days)          | ideas/analogy/<YYYY-MM-DD>
                       | ideas/constraints                      |
                       | morning-system/domain-list             |
investment_question    | watchlist/<TICKER>                     | (none)
gbrain_recall          | all namespaces (search, read-only)     | (none — recall metadata only)
no_do                  | guardrails/anti-patterns               | (none on daily delivery)
                       | guardrails/diagnostic-observations     | guardrails/anti-patterns (rare explicit consolidation/write mode)
                       | Kanban recent runs (last 7 days)       | guardrails/diagnostic-observations (rare explicit consolidation/write mode)
                       | session-derived feedback signals       |
gratitude              | (none)                                 | (none)
```

Note on `gbrain_recall`: this job searches broadly across all Gbrain content
but never writes. It tracks which notes have been recalled recently via a
lightweight local state file at `~/.hermes/morning/last_run/gbrain_recall.json`
(recall date per note ID). That file is local state, not a Gbrain write.

---

## 4. What Must Never Enter Gbrain

The following categories are **permanently prohibited** from Gbrain storage by
any morning job. Violation corrupts the signal quality of MT's long-term memory.

| Prohibited category | Why |
|---|---|
| Task progress or run outcome | Gbrain is not a run log. Use `~/.hermes/morning/last_run/` for session state. |
| Kanban task IDs as durable content | Task IDs are ephemeral. Manual pages may cite task IDs as temporary references/metadata, but durable Gbrain prose should reference task concepts, PRs, branches, or stable project artifacts instead. |
| Raw API responses or scraped HTML | Noise, not knowledge. Jobs must distill before writing. |
| Delivery confirmation records | "Sent weather brief at 6:00 AM" — useless in 30 days. |
| LLM chain-of-thought or reasoning traces | Intermediate reasoning is not knowledge. Final output only. |
| Secrets, tokens, API keys, passwords | Self-evident. Also enforced at the system level. |
| PII not owned by MT | MT's own notes are fine; notes about other people require explicit framing. |
| Error logs or stack traces | Belongs in `~/.hermes/morning/logs/`, not Gbrain. |
| Duplicate of what was written yesterday | Jobs must check before writing. Freshness is required. |
| Market prices, tickers as time-series data | Gbrain is not a time-series DB. Record materiality events, not price histories. |

---

## 5. Freshness and Recency Rules

These rules prevent Gbrain from becoming a noisy write-heavy store:

1. A `watchlist/<TICKER>` page must not be updated if the last entry is less than
   1 day old and no new material information was found.

2. `overnight_ideas` must not write today's idea page if today's date already has
   an entry (idempotent — one run per day max).

3. `cross_domain_analogy` must not write today's analogy page if it already exists.

4. `no_do` daily delivery must not write Gbrain. Rare explicit guardrail
   consolidation/write mode may update at most once per 7 days per pattern name
   after checking existing `last_triggered` and the BR-017 recurrence threshold.

5. The `gbrain_recall` job must not surface the same note within 14 days.
   Recency tracking lives in `~/.hermes/morning/last_run/gbrain_recall.json`.

---

## 6. Connection and Error Handling

All jobs that access Gbrain must:

1. Load `GBRAIN_DATABASE_URL` from `~/.gbrain/database_url` at job start.
   If the file does not exist or is empty, log the error and continue without
   Gbrain reads/writes — do not fail the entire job.

2. Treat Gbrain as **optional enrichment**, not a hard dependency.
   A job that cannot reach Gbrain should degrade gracefully, not skip delivery.

3. Wrap all Gbrain writes in a try/except. Log failures to
   `~/.hermes/morning/logs/<YYYY-MM-DD>/<job>.log`. Never surface Gbrain errors
   in the delivered message to MT.

4. Set a read timeout of 5 seconds per query. Set a write timeout of 10 seconds.
   If exceeded, skip the operation and log.

---

## 7. Implementation Notes for Agents

When implementing a job that reads Gbrain:

- Always query by vector similarity first (`gbrain search`), then read the
  matching page. Exact-title lookups are a fallback for known page names.
- Pass `--limit 5` or equivalent to avoid pulling large result sets.
- After reading, log the page title and match score to the job's local log file
  (not to Gbrain).

When implementing a job that writes Gbrain:

- Check the existing page content before writing. If the new content would be
  a near-duplicate (>80% overlap), skip the write.
- Always include a `date:` field in structured pages.
- Never overwrite the entire page if a partial update is sufficient — use
  append semantics where the client supports it.

---

## 8. Namespace Ownership Summary

```
Namespace                  | Owner    | Morning jobs may write?
---------------------------|----------|------------------------
morning-system/            | Manual   | No
watchlist/                 | jobs     | Yes — company_watchlist only
ideas/overnight/           | jobs     | Yes — overnight_ideas only
ideas/analogy/             | jobs     | Yes — cross_domain_analogy only
ideas/constraints          | Manual   | No
guardrails/anti-patterns   | Mixed    | Yes — no_do, conservatively
guardrails/scope-creep-log | Manual   | No
guardrails/diagnostic-obs  | Mixed    | Yes — no_do, conservatively
```

"Manual" means the page is edited by MT or a dedicated kanban task, never by
an automated morning cron job except as noted.

---

End of GBRAIN_CONVENTIONS.md
