# Security

Updated: <!-- YYYY-MM-DD -->

## What data is sensitive

<!-- List every category of sensitive data this project handles.
     For each: what it is, where it's stored, who can access it.
     Example:
     - API keys (OpenAI, Stripe, etc.) — env vars only, never logged, never in DB
     - User email addresses — Postgres users table, access restricted to API layer
     - No PII beyond email; no payment card data (Stripe handles that)
-->

## Threat model

<!-- What are the realistic attack vectors for this project?
     Agents read this to understand what to defend against.
     Example:
     - Prompt injection via user-supplied text fed to LLM calls
     - Leaked API keys via accidental commit or log output
     - Unauthorized access to the admin endpoints (no auth currently = known risk)
     - Dependency supply-chain attack via unpinned packages
-->

## Secrets handling protocol

<!-- The EXACT rules for this project. These override any agent default.
     Example:
-->

1. All secrets via environment variables. No exceptions.
2. Secret names (never values) live in `.env.example` only.
3. Real `.env` is gitignored. Confirm with `cat .gitignore | grep .env`.
4. Never log a secret, API key, token, or password — not even partially.
5. Never pass a secret as a CLI argument (it appears in shell history and
   `ps aux`). Pipe it in via stdin or read from env.
6. Secret scanning runs in CI. A commit that introduces a secret fails the
   pipeline.
7. If a secret is accidentally committed: rotate it IMMEDIATELY, then remove
   it from git history. See runbooks/rotate-leaked-secret.md.

## Authentication and authorization

<!-- Who can call what. Even if auth doesn't exist yet, document the plan.
     Example:
     - /api/public/* — unauthenticated, rate-limited by IP
     - /api/user/*   — requires valid JWT in Authorization header
     - /api/admin/*  — requires admin role in JWT claims
     - No auth yet on internal services (DB, Redis) — local-only, firewall blocks external
-->

## Dependencies and supply chain

<!-- How dependencies are managed to reduce supply-chain risk.
     Example:
     - Python deps: pinned in requirements.txt (exact versions, not ranges)
     - Node deps: package-lock.json committed, no --no-lockfile installs
     - Dependabot enabled on GitHub for automated CVE alerts
     - No `curl URL | sh` installs — ever
-->

## Known risks (accepted for now)

<!-- Security issues you know about but have decided to live with temporarily.
     Document them so agents don't try to "fix" them as side-quests,
     and so you remember to address them.
     Example:
     - Admin endpoints have no auth (acceptable for solo-dev phase, must fix before
       any external user gets access — tracked in BUGS.md)
     - No rate limiting on /api/research (low traffic, fix in v2)
-->

## Security checklist for PRs

Before any PR that touches auth, data handling, or external service calls:

- [ ] No secrets hardcoded or logged
- [ ] No new unauthenticated endpoints (or explicit approval if needed)
- [ ] User-supplied input is validated before use (especially in LLM prompts)
- [ ] No new dependencies without review
- [ ] `.env.example` updated if new env vars added
