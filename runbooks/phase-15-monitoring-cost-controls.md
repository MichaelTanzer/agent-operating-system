# Phase 15 — Monitoring and Cost Controls

Updated: 2026-05-11

This runbook implements the Phase 15 safety layer for the Flywheel/Hermes/VPS
agent stack. The goal is simple:

```text
You know what agents are running, what they cost, and how to stop them.
```

## Installed pieces

### Weekly/local report

Script:

```bash
~/bin/flywheel-spend-report
```

Manual run:

```bash
flywheel-spend-report --days 7
```

Output:

```text
~/dev/agent-memory/spend-reports/flywheel-phase15-report-YYYY-MM-DD-HHMM.md
~/dev/agent-memory/spend-reports/latest.md
~/dev/logs/flywheel-spend-report.log
```

The report tracks:

- Hermes sessions, token usage, and local recorded cost from `~/.hermes/state.db`
- model usage by tokens/cost
- failed or nonstandard Hermes session endings
- tmux sessions
- NTM sessions
- active worktrees, stale worktrees, dirty worktrees
- open GitHub PRs
- stale local branches
- br/bv task health where `.beads` is initialized
- open high-risk tasks where detectable from labels/title/body
- recent error lines in Hermes/Gbrain/Agent Mail logs
- Gbrain backup and `gbrain doctor` summary

Important limitation: provider dashboards remain the billing source of truth.
Hermes local cost data is an estimate or local record, not an enforcement cap.

### Circuit breaker / kill switch

Script:

```bash
~/bin/flywheel-killall
```

Dry run (default):

```bash
flywheel-killall
```

Actually stop matched agent sessions:

```bash
flywheel-killall --confirm
```

Stop everything optional too:

```bash
flywheel-killall --all
```

Log output:

```text
~/dev/logs/flywheel-killall-YYYY-MM-DD-HHMMSS.log
```

By default it targets only tmux sessions/windows matching agent-task naming
patterns, not arbitrary user shell sessions. Optional flags:

```bash
--stop-hermes       # stop Hermes gateway/service if running
--stop-agent-mail   # stop mcp-agent-mail user service
--pause-cron        # show Hermes cron/crontab; pause manually by ID
--pause-gbrain      # comment gbrain-backup.sh line from crontab, with backup
--all               # --confirm plus all optional actions
```

## Weekly operating loop

Run or review the weekly report:

```bash
flywheel-spend-report --days 7
```

Check the warnings at the top. For every warning, decide one of:

- fix now;
- create a br task;
- explicitly accept the risk for another week.

Minimum weekly checklist:

- [ ] Provider dashboards checked for spend and hard caps.
- [ ] `flywheel-spend-report` generated.
- [ ] Open PRs reviewed.
- [ ] Stale worktrees/branches cleaned up or justified.
- [ ] Failed runs inspected.
- [ ] Open high-risk tasks are known and intentionally scheduled/deferred.
- [ ] Gbrain backup exists and `gbrain doctor` is acceptable.
- [ ] Kill switch dry-run still works.

## Provider hard caps

Set caps directly in provider dashboards. Local scripts cannot enforce provider
billing limits.

Recommended starting point:

| Provider | Cap type | Suggested first cap |
|---|---|---:|
| OpenRouter | monthly spend | annoying but safe |
| OpenAI | monthly spend / project budget | annoying but safe |
| Anthropic | monthly spend | annoying but safe |
| Google/Gemini | project budget/quota | annoying but safe |
| Twilio, if later used | monthly spend | very low until needed |

Record the chosen caps here once set:

| Provider | Cap | Date set | Notes |
|---|---:|---|---|
| OpenRouter | TODO |  |  |
| OpenAI | TODO |  |  |
| Anthropic | TODO |  |  |
| Google/Gemini | TODO |  |  |

## App-level error logging

For real deployed apps, add Sentry or equivalent after the local loop works.
Do not wire production monitoring before you have:

- a deployment target;
- rollback instructions;
- environment variable documentation;
- a human-approved production deploy path.

Per project, record:

```text
Project:
Monitoring provider:
DSN/secret location: deployment platform or GitHub Secrets only
Alert route:
Rollback doc:
```

## Incident reports

Template:

```text
~/dev/repos/agent-operating-system/templates/INCIDENT_REPORT.md
```

For a real incident, copy it to the affected project or brain repo only if safe:

```bash
cp ~/dev/repos/agent-operating-system/templates/INCIDENT_REPORT.md \
  ~/dev/repos/<project>/INCIDENT-YYYY-MM-DD-XX.md
```

If the incident contains secrets, personal data, raw chat logs, or third-party
account data, do not put it in Gbrain. Write a sanitized summary instead.

## How to stop all agent sessions

First inspect:

```bash
flywheel-killall --dry-run
```

Then stop matched sessions:

```bash
flywheel-killall --confirm
```

If an agent is still running, inspect processes:

```bash
ps -u "$USER" -o pid,ppid,stat,etime,cmd | grep -E 'hermes|claude|codex|gemini|ntm|tmux' | grep -v grep
```

Kill only the specific runaway PID after recording it in an incident report.

## How to revoke API keys

1. Open provider dashboard.
2. Revoke the compromised key.
3. Remove/update it in `~/.hermes/.env` or the relevant service env file.
4. Restart affected services/sessions.
5. Run `hermes status --all`.
6. Create an incident report using `INCIDENT_REPORT.md`.

Never paste full API keys into prompts or Gbrain.

## How to disable cron jobs

Hermes cron:

```bash
hermes cron list
hermes cron pause <job-id>
```

System crontab:

```bash
crontab -l
crontab -e
```

The Gbrain backup cron line is intentionally not disabled by the kill switch
unless `--pause-gbrain` is passed.

## How to pause Gbrain ingestion

Current safe install uses project-memory-only Gbrain sync. There is no always-on
ingestion daemon yet.

To pause scheduled backups/sync-like cron entries:

```bash
flywheel-killall --confirm --pause-gbrain
```

To verify Gbrain health:

```bash
gbrain doctor
gbrain list | head
```

## Thresholds

Environment variables supported by `flywheel-spend-report`:

```bash
FLYWHEEL_WEEKLY_COST_WARN_USD=25
FLYWHEEL_WEEKLY_TOKEN_WARN=10000000
FLYWHEEL_STALE_BRANCH_DAYS=14
FLYWHEEL_STALE_WORKTREE_DAYS=7
```

Set these in the shell, crontab, or future systemd environment as needed.
