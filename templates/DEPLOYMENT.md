# Deployment

Updated: <!-- YYYY-MM-DD -->

## Where it runs

<!-- What infrastructure does this project use in production?
     Example:
     - Backend:  systemd service on Ubuntu 22.04 VPS (147.xxx.xxx.xxx)
     - Frontend: Vercel (project: my-project, auto-deploy OFF)
     - Database: Postgres 16 on same VPS, /var/lib/postgresql/
     - Domain:   example.com via Cloudflare (proxied)
-->

## How to deploy

<!-- The exact deploy procedure, copy-paste ready.
     If there are multiple components, one section per component.
-->

### Manual deploy procedure

```bash
# 1. Ensure you're on main and it's clean
git checkout main && git pull && git status

# 2. Run the full test suite — do not skip
# <test command from TESTING.md>

# 3. Deploy
# <exact deploy command(s)>

# 4. Run smoke tests
# <smoke test command(s)>
```

### CI/CD (if applicable)

<!-- Does GitHub Actions auto-deploy? When? To which environment?
     Example:
     - Push to main → deploys to staging automatically
     - Manual workflow dispatch required for production
     - Auto-deploy on push is DISABLED for AI agent branches (see AGENTS.md)
-->

## Environments

| Environment | URL | Branch | Deploy trigger |
|-------------|-----|--------|----------------|
| Production  | —   | main   | manual         |
| Staging     | —   | —      | —              |
| Local       | localhost:8000 | any | manual |

## Rollback procedure

<!-- The exact steps to roll back a bad deploy.
     This must be concrete enough to execute at 2am under stress.
     Example:
-->

**Time-to-rollback target:** <!-- e.g. < 5 minutes -->

```bash
# 1. Identify the last known-good commit
git log --oneline -10

# 2. Option A — Vercel: use dashboard or CLI instant rollback
vercel rollback

# 3. Option B — systemd: restart with prior binary / revert commit + redeploy
git revert HEAD --no-edit
git push origin main
# then re-run the deploy procedure above

# 4. Option C — database rollback (only if migrations were applied)
# <document the migration rollback command>
```

## Environment variables

<!-- Every env var the project needs in production.
     Names only — no values. Values live in the deploy target's secret store.
     Keep this in sync with .env.example.
-->

| Variable | Required | Description |
|----------|----------|-------------|
| —        | —        | —           |

## Smoke tests

<!-- Quick checks to run after every deploy to confirm it's alive.
     Copy-paste ready.
     Example:
     curl -sf https://example.com/api/health | jq .status
     # Expected: "ok"
-->

```bash
# <smoke test commands>
```

## First deploy checklist

Run this checklist the first time deploying to a new environment:

- [ ] All env vars set on the deploy target
- [ ] Auto-deploy on push is DISABLED (see AGENTS.md)
- [ ] Database migrations applied and verified
- [ ] Rollback procedure rehearsed (dry-run)
- [ ] Smoke tests pass
- [ ] CURRENT_STATE.md updated with deploy info
- [ ] CHANGELOG.md entry written

## Incident response

If production is down or degraded:

1. Check BUGS.md for known issues first
2. Check CURRENT_STATE.md for the most recent change
3. Run smoke tests to isolate the failure
4. If unclear, roll back first, investigate second
5. Log the incident in BUGS.md with date and symptoms
6. After resolution, add a DECISIONS.md entry if a pattern changed
