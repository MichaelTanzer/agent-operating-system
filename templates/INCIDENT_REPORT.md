# Incident Report

## ID

INC-YYYY-MM-DD-XX

## Severity

SEV-1 / SEV-2 / SEV-3 / SEV-4

## Status

Open / Mitigated / Resolved / Follow-up pending

## Summary

One sentence on what happened.

## Timeline

- HH:MM — Event
- HH:MM — Event
- HH:MM — Mitigation
- HH:MM — Resolution

## Trigger

What initiated the incident: agent action, deploy, external failure, human error,
credential issue, quota/cost spike, runaway process, data issue, etc.

## Impact

- Duration:
- Systems affected:
- Repos / projects affected:
- Data integrity:
- User impact:
- Cost impact:
- Security/privacy impact:

## Detection

How the incident was discovered:

- alert / report path:
- script/report involved:
- first signal:
- time to detection:

## Immediate response

What actions were taken to mitigate and resolve.

If the kill switch was used, record:

```bash
flywheel-killall --confirm <flags used>
```

Kill-switch log path:

```text
~/dev/logs/flywheel-killall-YYYY-MM-DD-HHMMSS.log
```

## Root cause

Why it happened, not just what happened.

## Contributing factors

Tools, processes, prompts, missing tests, missing approvals, or assumptions that
made the incident more likely or worse.

## What went well

Detection speed, response, tooling that helped.

## What did not go well

Gaps, slow response, missing alerts, missing docs, bad defaults.

## Evidence links

- PR(s):
- br task(s):
- tmux/NTM session(s):
- logs:
- Gbrain note(s):
- monitoring report:

## Action items

| Owner | Action | Due | Status |
|---|---|---|---|
|  |  |  |  |

## Lessons for the agent stack

Updates needed to: skills, policies, runbooks, CI rules, approvals, kill switch,
monitoring thresholds, provider caps, Gbrain policy.

Use this format for durable lessons:

```text
When <condition>, do <action>, because <reason>.
```

## Follow-up memory

- [ ] If safe under GBRAIN_POLICY.md, summarize this incident in
      `~/dev/repos/brain/retrospectives/` or `projects/<project>/incidents/`.
- [ ] Do not store secrets, raw chat logs, personal data, or third-party account
      data in Gbrain.
