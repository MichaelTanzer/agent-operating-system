# Gbrain Policy

Updated: 2026-05-13

Gbrain is installed as the searchable memory layer for the agent stack, but its
scope is intentionally narrow. Phase 12 proves Gbrain on safe project artifacts
before any wider ingestion is considered.

## Current decisions

- 2026-05-13: Gratitude prompt replies are not approved for Gbrain storage.
  They are private personal reflections by default. The gratitude job may emit
  metadata showing capture is disabled, and any future capture path must skip
  writes unless this policy is explicitly revised, MT grants consent for the
  specific reply, and a deletion smoke test covers the new source.

## What's allowed in the brain

- PLAN_FINAL.md per project
- CURRENT_STATE.md per project
- DECISIONS.md per project
- Retrospectives
- PR summaries after merge
- Task summaries from bead closure reports
- Architecture notes
- Gbrain policy/runbook summaries

## What's never in the brain without explicit policy revision

- Email content or metadata
- Calendar entries or invitations
- Slack, Discord, SMS, or DM content
- Financial account data: banks, brokerages, credit cards, invoices, payroll
- Browser history
- Personal photos, personal documents, or non-project notes
- Anything from a third party's account
- API keys, tokens, passwords, private keys, or any other credentials
- Raw chat exports unless a future policy explicitly allows a filtered subset

## Current installation boundary

- Tool repo: `~/gbrain`
- Brain content repo: `~/dev/repos/brain`
- Brain database: reported by `gbrain doctor` as `~/.gbrain/brain.pglite`
- Brain content repo is local-only. Do not configure a Git remote without a
  separate explicit approval.
- Dream cycle is disabled/deferred in Phase 12.
- Personal-data integrations are disabled/deferred in Phase 12.

## Decision protocol for adding new sources

Any new ingestion source requires all of the following:

1. Human approval per `policies/HUMAN_APPROVAL_POLICY.md`
2. A change to this policy naming the new allowed source
3. A backup/restore smoke test on the expanded corpus
4. A deletion smoke test for at least one item from the new source
5. A short entry in the relevant project's `DECISIONS.md`

If a source contains personal data by default, the default answer is no.

## When to delete

- A source file accidentally contained sensitive content
- A project is deprecated or abandoned and should leave the brain
- Search returns unexpected personal content
- Entity links connect project memory to personal entities unexpectedly
- Quarterly review finds accidentally-ingested content

Deletion must follow `runbooks/delete-gbrain-memory.md`.

## When to escalate to the user

Gbrain SHOULD surface, not auto-act on:

- Searches that return unexpected personal content
- Entity links that connect project memory to personal entities
- Disk usage growth beyond the Phase 12 budget
- Requests to configure Gmail, calendar, Twitter, voice, Slack, Discord, browser,
  or filesystem archive integrations
- Any request to push `~/dev/repos/brain` to a remote

## Disk budget

Phase 12 budget is 5 GB total for brain content, database, and backups. Alert when
combined usage exceeds 4 GB.

## Embedding provider status

No embedding provider is configured yet. Gbrain can run keyword search without
embeddings. Vector/hybrid search requires a future human decision on provider and
API key handling.
