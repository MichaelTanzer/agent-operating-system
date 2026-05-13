# PLAN_FINAL.md — MT Morning Briefing System

**Status:** Approved for implementation  
**Timezone:** America/New_York throughout  
**Author:** James Lafarge (kanban task t_f28b4274)

---

## 1. System Overview

Ten separate Hermes cron jobs deliver MT's morning context as independent messages. Each message targets a distinct cognitive mode; they are separate by design. A future bundling layer (3-group consolidation) is deferred. All jobs run via `hermes cronjob create` and are describe-only / recommend-only for anything touching the Kanban board or MT's agenda — no automatic mutations.

Runtime state and generated output live under `~/.hermes/morning/`. Source-controlled scripts, templates, and config live under `agent-operating-system/morning-briefing/`. No secrets are committed to git.

---

## 2. Directory Layout

```
agent-operating-system/
  morning-briefing/
    PLAN_FINAL.md                  ← this file
    config/
      jobs.yaml                    ← all job specs (schedules, flags, output contracts)
      watchlist.yaml               ← company ticker + metadata (source-controlled)
    scripts/
      weather.py                   ← DC weather fetch + format
      watchlist_digest.py          ← company/industry news scraper + formatter
      kanban_brief.py              ← board introspection + summary builder
      kanban_cleanup.py            ← stale-task detector + cleanup proposal builder
      overnight_ideas.py           ← idea generator (reads Kanban + Gbrain)
      investment_question.py       ← single question generator
      gbrain_recall.py             ← surface one Gbrain note
    templates/
      weather.j2                   ← weather message template
      watchlist.j2                 ← watchlist digest template
      kanban_brief.j2              ← morning kanban brief template
      kanban_cleanup.j2            ← cleanup proposal template
      overnight_ideas.j2           ← idea buckets template
```

```
~/.hermes/morning/                 ← runtime state, NOT in git
  config.yaml                      ← local overrides (delivery channel, watchlist path)
  last_run/
    weather.json
    watchlist.json
    kanban_brief.json
    kanban_cleanup.json
    overnight_ideas.json
    investment_question.json
    gbrain_recall.json
    no_do.json
    gratitude.json
    cross_domain.json
  logs/
    YYYY-MM-DD/
      <job>.log
```

---

## 3. Config Format

### agent-operating-system/morning-briefing/config/jobs.yaml

```yaml
system:
  timezone: America/New_York
  delivery: telegram          # platform name; home channel unless overridden per-job
  state_dir: ~/.hermes/morning
  watchlist_path: morning-briefing/config/watchlist.yaml

jobs:
  dc_weather:
    enabled: true
    cadence: daily
    cron: "0 6 * * *"          # 6:00 AM ET
    implementation: script     # pure Python fetch, no LLM needed
    script: morning-briefing/scripts/weather.py
    template: morning-briefing/templates/weather.j2
    output_contract:
      max_lines: 7
      format: plain
      fields: [high_f, low_f, umbrella, aqi, pollen, stroller_ok, material_alert]

  company_watchlist:
    enabled: true
    cadence: weekday
    cron: "5 6 * * 1-5"        # 6:05 AM ET, Mon–Fri
    implementation: agent      # needs reasoning to filter material vs. noise
    script: morning-briefing/scripts/watchlist_digest.py
    output_contract:
      max_items: 10
      format: bullet
      fields: [company, ticker, headline, source_tier, materiality_signal]
      filter: material_only

  kanban_morning_brief:
    enabled: true
    cadence: weekday
    cron: "10 6 * * 1-5"       # 6:10 AM ET
    implementation: agent
    script: morning-briefing/scripts/kanban_brief.py
    output_contract:
      format: structured
      sections:
        - backlog_counts
        - tasks_needing_mt
        - stuck_or_risky
        - suggested_actions    # 3–5 items, recommend-only
        - completions_since_last_run
      mutations_allowed: false

  kanban_cleanup_proposal:
    enabled: true
    cadence: weekly
    cron: "0 8 * * 1"          # 8:00 AM ET Monday
    implementation: agent
    script: morning-briefing/scripts/kanban_cleanup.py
    output_contract:
      format: structured
      sections:
        - stale_tasks          # idle > 7 days
        - duplicate_candidates
        - oversized_tasks
        - wrong_profile_assignments
        - orphaned_chains
        - archivable_items
      mutations_allowed: false

  overnight_ideas:
    enabled: true
    cadence: weekday
    cron: "15 6 * * 1-5"       # 6:15 AM ET
    implementation: agent
    script: morning-briefing/scripts/overnight_ideas.py
    output_contract:
      buckets: 4
      ideas_per_bucket: 3
      sentences_per_idea: 2
      format: grouped_bullets
      auto_task_creation: false
      buckets_spec:
        - id: kanban_good_to_great
          label: "Kanban good → great"
          reads_kanban: true
          reads_gbrain: false
        - id: extend_mt_capabilities
          label: "Extend MT's capabilities"
          reads_kanban: false
          reads_gbrain: true
        - id: coding_stack_efficacy
          label: "Coding stack efficacy"
          reads_kanban: false
          reads_gbrain: true
        - id: new_project_ideas
          label: "New project ideas"
          reads_kanban: false
          reads_gbrain: true

  cross_domain_analogy:
    enabled: true
    cadence: weekly
    cron: "0 20 * * 0"         # 8:00 PM ET Sunday
    implementation: agent
    output_contract:
      format: essay_seed
      max_paragraphs: 3
      domains:
        - investment research craft
        - AI agent architectures
        - psychoanalytic theory
        - ceramics
        - art history
        - philosophy and economics
        - fatherhood
        - TanzerBot

  investment_question:
    enabled: true
    cadence: weekday
    cron: "20 6 * * 1-5"       # 6:20 AM ET
    implementation: agent
    script: morning-briefing/scripts/investment_question.py
    output_contract:
      format: single_question
      max_sentences: 2
      must_be_researchable: true
      tied_to: watchlist_or_tanzerbot

  gbrain_recall:
    enabled: true
    cadence: weekday
    cron: "25 6 * * 1-5"       # 6:25 AM ET
    implementation: agent
    script: morning-briefing/scripts/gbrain_recall.py
    output_contract:
      format: single_note
      max_lines: 5
      include_origin_date: true

  no_do:
    enabled: true
    cadence: weekday
    cron: "30 6 * * 1-5"       # 6:30 AM ET
    implementation: agent
    output_contract:
      format: single_item
      max_sentences: 2
      label: "One Thing to Not Do Today"

  gratitude:
    enabled: true
    cadence: daily
    cron: "35 6 * * *"         # 6:35 AM ET, daily
    implementation: script     # simple fixed prompt, no reasoning needed
    output_contract:
      format: prompt_message
      text: "What are three things you're grateful for?"
      expects_response: true
```

### ~/.hermes/morning/config.yaml (runtime, not in git)

```yaml
# Local overrides. This file is NOT committed to git.
delivery:
  platform: telegram
  # channel: optional override from default home channel

watchlist_path: ~/dev/repos/agent-operating-system/morning-briefing/config/watchlist.yaml
gbrain_db_url: "${GBRAIN_DATABASE_URL}"   # reference env var; value not stored here
```

---

## 4. Approved Job Specs

### 4.1 Daily DC Weather

- Cadence: daily, 6:00 AM ET
- Implementation: script (no LLM — deterministic data fetch)
- Sources: wttr.in for weather; airnow.gov or OpenAQ for AQI; pollen.com or equivalent for pollen
- Output contract: 4–7 lines max
  - Line 1: High/low temp (°F)
  - Line 2: Conditions + umbrella call (yes/no)
  - Line 3: AQI + pollen level
  - Line 4: Stroller suitability (brief phrase)
  - Line 5 (conditional): Material alerts only (heat advisory, air quality action day, etc.)
- Dry-run: `python morning-briefing/scripts/weather.py --dry-run`

### 4.2 Weekday Company + Industry Watchlist Digest

- Cadence: weekday, 6:05 AM ET
- Implementation: agent (LLM needed to filter materiality)
- Companies (24): Aon, ArcBest, Arthur Gallagher, Brown & Brown, Bureau Veritas, CH Robinson, DSV, Eurofins, Forward Air, GXO, Intertek, Kuehne+Nagel, Mainfreight, Marsh, ODFL, RXO, Ryan Specialty, Saia, SGS, Baldwin Insurance, UL Solutions, WTW, XPO, plus cross-industry (logistics, insurance, testing/inspection/certification)
- Source tiers: Tier 1 = SEC filings / earnings; Tier 2 = Bloomberg/Reuters/WSJ; Tier 3 = company IR press releases; Tier 4 = trade press
- Output contract: material items only, max 10 bullets, source-tier tagged, Gbrain-integrated (check prior coverage before surfacing)
- Gbrain integration: query Gbrain for recent notes on each company before including; surface "first time in X days" context when available
- Dry-run: `python morning-briefing/scripts/watchlist_digest.py --dry-run --company AON`

### 4.3 Weekday Kanban Morning Brief

- Cadence: weekday, 6:10 AM ET
- Implementation: agent
- Data source: `hermes kanban list` + task details via Kanban API
- Output sections (in order):
  1. Backlog counts by status (ready / in-progress / blocked / todo)
  2. Tasks needing MT (blocked on human input, or assigned to default with question)
  3. Stuck or risky tasks (running > 2x expected, no heartbeat in 4h, retry count ≥ 2)
  4. Suggested actions: 3–5 concrete next steps, recommend-only, no mutations
  5. Completions since last run (task IDs + one-line summaries)
- Constraint: NO board mutations — read-only
- Dry-run: `python morning-briefing/scripts/kanban_brief.py --dry-run`

### 4.4 Weekly Kanban Cleanup Proposal

- Cadence: weekly, 8:00 AM ET Monday
- Implementation: agent
- Checks:
  - Stale tasks: last activity > 7 days, status not done/archived
  - Duplicate candidates: title similarity > 0.85 (TF-IDF or embedding)
  - Oversized tasks: > 3 child tasks and no clear phase structure
  - Wrong-profile assignments: heuristic based on title keywords vs. profile capabilities
  - Orphaned chains: tasks with parents all done but child never moved to ready
  - Archivable items: done > 30 days with no downstream dependents
- Output: Proposal document only — MT approves/rejects in reply
- Constraint: NO mutations, NO archiving, NO reassignment without explicit MT approval
- Dry-run: `python morning-briefing/scripts/kanban_cleanup.py --dry-run`

### 4.5 Weekday Overnight Ideas

- Cadence: weekday, 6:15 AM ET
- Implementation: agent
- 4 buckets × 3 ideas × 2 sentences each:
  1. Kanban good → great (reads current board state)
  2. Extend MT's capabilities (uses Gbrain)
  3. Coding stack efficacy (uses Gbrain)
  4. New project ideas (uses Gbrain; domains: psychoanalysis, ceramics, art history, philosophy/economics, investment research craft, TanzerBot, AI agent architectures, fatherhood)
- Constraint: NO auto-task creation; ideas are for MT to evaluate; no ranking within buckets
- Dry-run: `python morning-briefing/scripts/overnight_ideas.py --dry-run`

### 4.6 Weekly Cross-Domain Analogy Prompt

- Cadence: weekly, 8:00 PM ET Sunday
- Implementation: agent
- Mechanism: forced domain contact — pick two domains from the master list and generate an essay seed exploring structural analogies
- Domain list: investment research craft, AI agent architectures, psychoanalytic theory, ceramics, art history, philosophy and economics, fatherhood, TanzerBot
- Output: 2–3 paragraphs suitable as an essay opening or letter to MT
- Dry-run: set `MORNING_DRY_RUN=1` in env, runs agent with output to stdout only

### 4.7 One Investment Question of the Day

- Cadence: weekday, 6:20 AM ET
- Implementation: agent
- Format: single question, max 2 sentences, must be specific and researchable
- Tied to: current watchlist companies or TanzerBot's active research threads (read from Gbrain)
- Not a market-regime question; not a macro generality — must be company/sector-anchored
- Dry-run: `python morning-briefing/scripts/investment_question.py --dry-run`

### 4.8 Gbrain Recall

- Cadence: weekday, 6:25 AM ET
- Implementation: agent
- Mechanism: query Gbrain with today's date range and MT's interest domains; surface one note that has not been recalled recently
- Output: 3–5 lines with origin date included
- Dry-run: `python morning-briefing/scripts/gbrain_recall.py --dry-run`

### 4.9 One Thing to Not Do

- Cadence: weekday, 6:30 AM ET
- Implementation: agent
- Format: single item, 1–2 sentences, framed as a guardrail or anti-priority
- Draws from: recent Kanban patterns (scope creep, architecture-as-avoidance), Gbrain memory, watchlist themes
- Not motivational — diagnostic and specific
- Dry-run: set `MORNING_DRY_RUN=1`

### 4.10 Gratitude Prompt

- Cadence: daily (including weekends), 6:35 AM ET
- Implementation: script (no LLM needed — fixed text)
- Output: "What are three things you're grateful for?"
- Delivered as a separate message; expects a response from MT (no auto-processing of reply)
- Dry-run: `python morning-briefing/scripts/gratitude.py --dry-run` (prints message to stdout)

---

## 5. Script-vs-Agent Decision

| Job | Decision | Rationale |
|---|---|---|
| DC Weather | Script | Deterministic data fetch + template render; no judgment needed |
| Company Watchlist | Agent | Materiality filtering and source-tier reasoning require LLM |
| Kanban Morning Brief | Agent | Board summarization and risk flagging require judgment |
| Kanban Cleanup | Agent | Duplicate detection and priority assessment require reasoning |
| Overnight Ideas | Agent | Creative generation tied to real board state requires LLM |
| Cross-Domain Analogy | Agent | Generative; output quality depends on LLM creativity |
| Investment Question | Agent | Tight quality bar (researchable, company-anchored) needs LLM |
| Gbrain Recall | Agent | Relevance ranking and surface decision requires judgment |
| One Thing to Not Do | Agent | Diagnosis requires reasoning across multiple signals |
| Gratitude Prompt | Script | Fixed text; no reasoning needed |

---

## 6. Cron Schedules (America/New_York)

```
6:00 AM daily         dc_weather           (all 7 days)
6:05 AM Mon–Fri       company_watchlist
6:10 AM Mon–Fri       kanban_morning_brief
6:15 AM Mon–Fri       overnight_ideas
6:20 AM Mon–Fri       investment_question
6:25 AM Mon–Fri       gbrain_recall
6:30 AM Mon–Fri       no_do
6:35 AM daily         gratitude            (all 7 days)
8:00 AM Monday        kanban_cleanup_proposal
8:00 PM Sunday        cross_domain_analogy
```

Stagger is deliberate: 5-minute gaps prevent concurrent load and keep messages sequential in the Telegram thread.

---

## 7. Gbrain Integration Plan

Gbrain (local PostgreSQL + pgvector, DB: gbrain) is available at the URL stored in `~/.gbrain/database_url` and `~/.gbrain/config.json`. The env var `GBRAIN_DATABASE_URL` should be set from that file in each agent job's environment.

Integration points per job:

**Watchlist Digest:** Before including a company item, query Gbrain for notes tagged with that ticker. If a similar item was surfaced in the last 3 days, skip or flag as "revisit." Write a note back to Gbrain when a new material item is delivered.

**Overnight Ideas:** Buckets 2, 3, 4 query Gbrain for relevant project notes and memory before generating ideas. This gives ideas grounding in MT's actual history rather than generic generation.

**Investment Question:** Query Gbrain for active TanzerBot research threads and recent watchlist queries. The question should extend or probe an existing thread, not start from scratch.

**Gbrain Recall:** Query with current date, all domains, recency exclusion (skip notes recalled in last 14 days). Score by: age since last recall + relevance to current Kanban activity.

**One Thing to Not Do:** Read recent Kanban run history (last 7 days) + Gbrain notes tagged with "anti-pattern" or "scope-creep." Generate the guardrail from patterns, not abstractions.

---

## 8. Phased Rollout

### Phase 1 — Foundations (implement first)
Jobs: `dc_weather`, `gratitude`, `no_do`, `overnight_ideas`

Rationale: Weather and gratitude are highest signal-to-complexity. `no_do` is low-stakes and fast to implement. `overnight_ideas` exercises Gbrain + Kanban reads early so issues surface before Phase 2.

Deliverables:
- Directory scaffold in agent-operating-system
- `config/jobs.yaml` with all 10 jobs defined (disabled flag for phases 2+3)
- `~/.hermes/morning/` state dir initialized
- Phase 1 scripts implemented and tested
- 4 cron jobs registered with `hermes cronjob create`
- Dry-run commands verified for all 4

### Phase 2 — Board Integration
Jobs: `kanban_morning_brief`, `kanban_cleanup_proposal`

Prerequisite: Phase 1 running stably for at least 3 days

Deliverables:
- `kanban_brief.py` and `kanban_cleanup.py` scripts
- Cron jobs registered and tested
- Verified recommend-only behavior (no board mutations observable in audit log)

### Phase 3 — Research Layer
Jobs: `company_watchlist`, `investment_question`, `gbrain_recall`, `cross_domain_analogy`

Prerequisite: Phase 2 stable; Gbrain confirmed accessible from cron job environment

Deliverables:
- `watchlist_digest.py` with 24-company list loaded from `config/watchlist.yaml`
- `investment_question.py` and `gbrain_recall.py` reading from Gbrain
- `cross_domain_analogy` cron job registered for Sunday 8 PM
- All Phase 3 dry-runs passing

---

## 9. Dry-Run Commands

Each script supports `--dry-run` (prints output to stdout, delivers nothing, writes nothing to `~/.hermes/morning/`). Agent jobs use env var `MORNING_DRY_RUN=1` for the same effect.

```bash
# Phase 1
python morning-briefing/scripts/weather.py --dry-run
python morning-briefing/scripts/overnight_ideas.py --dry-run
MORNING_DRY_RUN=1 hermes run-job no_do
python morning-briefing/scripts/gratitude.py --dry-run

# Phase 2
python morning-briefing/scripts/kanban_brief.py --dry-run
python morning-briefing/scripts/kanban_cleanup.py --dry-run

# Phase 3
python morning-briefing/scripts/watchlist_digest.py --dry-run --company AON
python morning-briefing/scripts/investment_question.py --dry-run
python morning-briefing/scripts/gbrain_recall.py --dry-run
MORNING_DRY_RUN=1 hermes run-job cross_domain_analogy
```

To test the full morning cluster in sequence (Phase 1 only, no delivery):
```bash
MORNING_DRY_RUN=1 MORNING_PHASE=1 python morning-briefing/scripts/run_all.py
```

---

## 10. Cron Registration Commands

These are the `hermes cronjob create` commands for Phase 1. Phases 2 and 3 follow the same pattern with the appropriate schedule and prompt.

```bash
# DC Weather (daily 6:00 AM ET)
hermes cronjob create \
  --name "dc-weather" \
  --schedule "0 6 * * *" \
  --prompt "Run weather.py for DC and deliver a 4-7 line weather brief per the output contract in morning-briefing/config/jobs.yaml. Dry-run if MORNING_DRY_RUN=1." \
  --no-agent \
  --script "~/dev/repos/agent-operating-system/morning-briefing/scripts/weather.py"

# Gratitude (daily 6:35 AM ET)
hermes cronjob create \
  --name "gratitude-prompt" \
  --schedule "35 6 * * *" \
  --no-agent \
  --script "~/dev/repos/agent-operating-system/morning-briefing/scripts/gratitude.py"

# One Thing to Not Do (weekday 6:30 AM ET)
hermes cronjob create \
  --name "no-do" \
  --schedule "30 6 * * 1-5" \
  --prompt "Generate one anti-priority guardrail for MT today. Read recent Kanban run history (last 7 days) and Gbrain notes tagged anti-pattern. Single item, 1-2 sentences, diagnostic not motivational. Deliver to telegram."

# Overnight Ideas (weekday 6:15 AM ET)
hermes cronjob create \
  --name "overnight-ideas" \
  --schedule "15 6 * * 1-5" \
  --prompt "Generate 4 buckets × 3 ideas × 2 sentences each for MT. Buckets: (1) Kanban good→great [read current board], (2) extend MT capabilities [use Gbrain], (3) coding stack efficacy [use Gbrain], (4) new project ideas [use Gbrain; domains: psychoanalysis, ceramics, art history, philosophy/economics, investment research craft, TanzerBot, AI agent architectures, fatherhood]. No ranking. No auto-task creation. Deliver to telegram."
```

Full registration commands for Phases 2 and 3 will be generated by the Phase 2/3 implementation tasks.

---

## 11. Acceptance Criteria

This plan is complete when:

- [ ] `agent-operating-system/morning-briefing/` directory exists with all subdirectories
- [ ] `config/jobs.yaml` defines all 10 jobs with schedule, implementation type, and output contract
- [ ] `config/watchlist.yaml` contains all 24 companies with ticker and sector
- [ ] All Phase 1 dry-run commands execute without error
- [ ] Phase 1 cron jobs registered and visible in `hermes cronjob list`
- [ ] `~/.hermes/morning/` state directory exists with documented structure
- [ ] No secrets in any committed file
- [ ] This PLAN_FINAL.md is merged to main via PR

---

## 12. First Execution Wave

After Phase 1 cron jobs are registered:

1. Run `weather.py --dry-run` to confirm DC weather fetch
2. Run `gratitude.py --dry-run` to confirm message text
3. Manually trigger `hermes cronjob run <overnight-ideas-id>` for first live run
4. Confirm delivery in Telegram
5. Check `~/.hermes/morning/last_run/` for output JSON artifacts
6. If all pass: enable `no_do` cron job and let the full Phase 1 cluster run naturally at 6 AM next weekday

---

## 13. Out of Scope (Deferred)

- Calendar + Energy Map
- Personal Logistics / Family Window
- Read/Skim/Ignore Queue
- 3-group message bundling (Practical / Work-Research / Creative-Reflective)
- Auto-reply processing for Gratitude
- Slack/Discord delivery (Telegram only for now)

---

End of PLAN_FINAL.md
