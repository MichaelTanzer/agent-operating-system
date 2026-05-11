---
name: flywheel-deploy-and-maintenance
version: 1.0.0
description: >-
  Run Phase 5 of Jeffrey Emanuel-style Agent Flywheel workflow: ship the
  steady-state codebase produced by Phases 3-4 to production, then keep
  the project (and a fleet of projects) moving forward via a daily
  autopilot rhythm using RU, NTM, BV, Beads, Agent Mail, DCG, and SLB.
  Use after the user has reached steady state (Phase 4 complete) and is
  ready to deploy, plus thereafter as an ongoing maintenance protocol.
  Designed for the Hermes harness running against a VPS-hosted Agent
  Flywheel environment.
metadata:
  category: operations
  tags:
    - flywheel
    - deploy
    - maintenance
    - autopilot
    - production
    - vercel
    - cloudflare
    - supabase
    - ru
    - ntm
    - agent-mail
    - beads
    - bv
    - dcg
    - slb
    - agent-harness
    - hermes
    - vps
    - rollback
    - smoke-tests
    - frontier-models
  intended_harnesses:
    - Hermes
    - OpenClaw
    - Claude Code Routines (for scheduled autopilot)
    - Generic markdown skill harnesses
  slash_commands:
    - flywheel-deploy-and-maintenance
    - flywheel-phase-5
    - deploy-and-maintain
    - autopilot
---

# Flywheel Phase 5 — Deploy & Maintenance Skill

## Purpose

This skill operationalizes **Phase 5: Deploy & Maintenance** of a Flywheel-style agentic software workflow. It has two distinct tracks that share an artifact directory and a set of safety primitives:

* **Track A — Initial Deploy.** A one-shot, gated push of the steady-state codebase to a production target (Vercel for web apps, a systemd service on the VPS for backends, a scheduled job runner for pipelines, etc.), with smoke tests and a rehearsed rollback path.
* **Track B — Daily Maintenance (Autopilot Mode).** An ongoing daily/weekly rhythm where `ru sync` brings every project up to date, NTM spawns agents across the fleet, the swarm picks up new beads, and `ru agent-sweep` commits the day's work with AI-generated messages. The operator's job in this track is light — a few small checks per day — but persistent.

Phases 1-4 are projects with endings. Phase 5 is the rest of the project's life. The two tracks reflect that: an initial deploy that happens once, and a maintenance rhythm that runs forever (or until the project is sunset).

## A note on prompt provenance

Phases 1-4 use prompts that are direct citations from Jeffrey Emanuel's canonical library on agent-flywheel.com and the `Dicklesworthstone/agent_flywheel_clawdbot_skills_and_integrations` GitHub repo. Phase 5 in the canonical source is described as a **rhythm using existing tools** (RU, NTM, Vercel/Cloudflare/Supabase CLIs, DCG, SLB) rather than as a fixed prompt library.

This skill therefore uses two kinds of prompts:

1. **Canonical prompts**, byte-identical to the Phase 3-4 library. Reused here include the **Commit Changes**, **Post-Compaction**, and **Random Exploration** prompts.
2. **Composed prompts**, written for this skill in the canonical voice (`Use ultrathink`, `AGENTS dot md` phrasing, anti-purgatory framing). Each composed prompt is labelled `[COMPOSED]` so it is never confused with a canonical citation. Composed prompts are intentionally short and sit inside the same operational scaffolding as the canonical ones.

If you want to swap a composed prompt for one of your own, do so — the skill's structure doesn't depend on the exact composed text, only on the canonical citations.

## Why this protocol exists

A Phase 4 steady state and a healthy production system are not the same thing. The transition from "the swarm thinks this is clean" to "real users hit this and it survives" is where most agent-built projects fail.

Common failure modes this protocol is calibrated to address:

* **Hardcoded values that work in dev and break in prod.** Secrets, API endpoints, database URLs, feature flags. Pre-flight catches them before deploy.
* **Untested rollback.** A rollback path that has never been exercised is a rollback path that doesn't exist. Track A includes a deliberate rollback rehearsal.
* **Silent autopilot drift.** A swarm running unattended for weeks will eventually do something the operator wouldn't have approved. The autopilot rhythm includes daily and weekly checkpoints with explicit gates.
* **Fleet-scale chaos.** Once the user is running 5+ projects in parallel, manual project-by-project management is impossible. RU + agent-sweep + Agent Mail file reservations are the canonical solution.
* **Production-grade safety.** DCG blocks destructive commands, SLB requires human approval for risky ones. Both become more important in Phase 5 than they were in dev.

The leverage in this phase is *not* in the prompts. It is in (a) gating the initial deploy with real preflight + smoke tests + rollback rehearsal, (b) running the autopilot rhythm consistently rather than skipping days, and (c) keeping the operator presence light enough that it actually happens daily.

## CURRENT_STATE.md — required update at end of every session

Before any session using this skill ends, CURRENT_STATE.md MUST be updated:

1. Set "Updated:" to today's date
2. Move completed deploy/maintenance work into "Recently completed"
3. Update "Working" to reflect what is now confirmed live in production
4. Update "Broken" and "Risks" with anything surfaced during the run
5. Set "Next recommended action" to the next autopilot action or known follow-up

For Track A: update after every successful deploy and after rollback rehearsal.
For Track B: update at end of every daily autopilot run.

This is non-negotiable. The next session (human or agent) reads CURRENT_STATE.md
first. If it is stale, the next session starts blind.

---

## When to use this skill

Use this skill when:

* `06-steady-state-evidence.md` from Phase 3-4 exists and the codebase is committed and pushed.
* The user is ready to deploy to a real production target (or has already deployed and wants to start the maintenance rhythm).
* The user says: "ship it," "deploy to prod," "start the autopilot," "run the morning routine," "run Phase 5," or any equivalent.
* The user is running an existing fleet and wants to extend autopilot to a new project.

Do not use this skill for:

* Projects without a Phase 4 steady state. Run `flywheel-swarm-implementation-and-polish` first.
* Production incidents requiring synchronous human response. This skill is for *steady* production operation; an active SEV is a different mode.
* Projects deliberately running on a different deploy stack the user has not configured (e.g., AWS Lambda when AGENTS.md describes Vercel). Update AGENTS.md first.
* Projects where the user has not consented to autopilot. A swarm running unattended every morning is a real budget commitment.

## Prerequisites

Before running this skill, verify:

1. **Phase 4 steady-state evidence exists.** `.flywheel/phase-3-4/06-steady-state-evidence.md` is present and shows a clean rotation. If review was waived, the user has acknowledged the risk in writing.
2. **Repo is committed and pushed.** `git status --porcelain` returns clean; remote is up to date.
3. **Deploy target is identified and documented in AGENTS.md.** Vercel project ID, Cloudflare zone, Supabase project, systemd service name — whatever applies. AGENTS.md should also document the rollback procedure.
4. **Deploy CLIs are installed and authenticated** on the VPS or Hermes-driven shell:

   ```bash
   vercel --version && vercel whoami        # if web app
   wrangler --version && wrangler whoami    # if Cloudflare
   supabase --version                       # if Supabase
   gh auth status                           # for repo / actions
   systemctl --version                      # if VPS service
   ```

5. **Secrets are provisioned, not hardcoded.** Check the repo for accidentally-committed secrets (`gitleaks detect`, `trufflehog`, or equivalent). The deploy target has all required env vars set.
6. **DCG is installed** and active on the VPS for any agent that will run shell commands in production paths. `which dcg` returns a path; DCG hooks are wired into the relevant CLIs.
7. **SLB is installed and configured.** Two-person rule for dangerous operations is wired in.
8. **For Track B (autopilot):** RU is installed (`ru --version`), the user has the project rooted under RU's tracked tree, and the cron/scheduler that will trigger the morning routine is running. If using Claude Code Routines, the routine is created and pinned to the right repo.
9. **Backup state captured.** Before the first prod deploy, `git rev-parse HEAD` is recorded as the rollback target, and the database (if any) has a snapshot.

If any prerequisite is missing, stop and surface it. Production failures from skipped prereqs are dramatically more expensive than dev failures.

## Required capabilities

The Hermes harness (or whichever harness drives this skill) must be able to:

1. SSH or otherwise connect to the VPS hosting the swarm and the deploy origin.
2. Run deploy CLIs (`vercel`, `wrangler`, `supabase`, `gh`, `systemctl`, etc.) and capture structured output.
3. Send commands to NTM-managed tmux sessions for autopilot work.
4. Read and write files under `.flywheel/phase-5/`.
5. Trigger or observe a scheduled task (cron, systemd timer, or Claude Code Routine) without holding a long-lived foreground process.
6. Pause for SLB approval prompts when DCG/SLB blocks an operation, and surface them to the user.
7. Capture deploy output, smoke test output, and rollback rehearsal output verbatim for the audit trail.

If any capability is unavailable, surface the limitation rather than degrade silently.

## The two tracks

```text
                    +-------------------------------------+
                    |  Phase 4 steady-state codebase      |
                    +-------------------------------------+
                                     |
                                     v
                    +-------------------------------------+
                    |  Track A — Initial Deploy           |
                    |  (one-shot; runs once per project)  |
                    +-------------------------------------+
                                     |
                                     v   (after first successful deploy)
                    +-------------------------------------+
                    |  Track B — Daily Maintenance        |
                    |  (recurring; runs forever)          |
                    +-------------------------------------+
                                     |
                                     v   (when autopilot surfaces a real issue)
                          back to Phase 1 / Phase 2 / Phase 3-4
```

Track A and Track B share the same artifact directory but are otherwise independent. The skill can resume into either track based on the artifact state.

## Artifact directory

```text
.flywheel/phase-5/
├── 00-deploy-target.md           Deploy stack, target URLs, rollback procedure
├── 01-preflight.md               Pre-deploy checks and their results
├── 02-deploy-runs/               One folder per production deploy
│   ├── deploy-001-<timestamp>/
│   │   ├── git-head.txt          HEAD commit at deploy time
│   │   ├── deploy.log            Verbatim deploy command output
│   │   ├── smoke-tests.log       Smoke test output
│   │   ├── rollback-rehearsal.log  Output of rollback dry-run (first deploy only)
│   │   └── outcome.md            Success/failure + notes
│   └── deploy-002-...
├── 03-autopilot/
│   ├── morning-prompt.txt        The exact morning autopilot prompt sent each day
│   ├── runs/
│   │   ├── 2026-05-09/           One folder per autopilot day
│   │   │   ├── ru-sync.log
│   │   │   ├── ntm-spawn.log
│   │   │   ├── morning-prompt-sent.txt
│   │   │   ├── operator-checkins.md
│   │   │   ├── eod-sweep.log
│   │   │   └── day-summary.md
│   │   └── ...
│   └── weekly/
│       ├── 2026-W19-review.md
│       └── ...
├── 04-incidents.md               Append-only log of autopilot escalations
├── 05-rollbacks.md               Append-only log of any production rollbacks
└── REPORT_FINAL.md               Latest deploy report + autopilot health summary
```

`REPORT_FINAL.md` is unusual for this skill: unlike Phases 1-4, it is *living* — overwritten each significant operation rather than written once. Treat it as the current state of the world rather than a final deliverable.

## Resumability

```text
If 00-deploy-target.md is missing:
  resume at the start of Track A.

If 00-deploy-target.md exists but 02-deploy-runs/ is empty or contains
only failed deploys:
  resume at Track A from where the prior run failed.

If 02-deploy-runs/ contains at least one successful deploy and the user
asked to "deploy" or "ship":
  this is a re-deploy. Resume at Track A, segment A3 (skip A1-A2 unless
  the deploy target has changed).

If 02-deploy-runs/ contains at least one successful deploy and the user
asked to "run the morning routine," "start autopilot," or anything
recurring:
  resume at Track B.

If 03-autopilot/runs/ has a run for today's date already:
  ask the user before re-running — daily autopilot is meant to be
  idempotent but not free.

If a prior run aborted mid-way (deploy.log exists but outcome.md is
missing):
  show the user the partial log; ask whether to retry, roll back, or
  investigate.
```

When resuming, say:

```text
Looks like we left off at [track / segment]. The deploy target is
[target]. The most recent successful deploy was [timestamp], and the
last autopilot run was [timestamp]. I can [resume / restart / start
fresh].
```

---

# Track A — Initial Deploy

## Segment A1 — Deploy Preflight

### A1 goal

Catch every cheap failure before any production change happens. Pre-flight failures are nearly free; mid-deploy failures are expensive; post-deploy failures discovered by users are catastrophic.

### Procedure

1. Confirm Phase 4 steady-state evidence:

   ```bash
   test -f .flywheel/phase-3-4/06-steady-state-evidence.md
   git status --porcelain
   git rev-parse HEAD
   git fetch && git status -uno
   ```

   Repo must be clean and up to date with origin.

2. Identify and document the deploy target. Write `00-deploy-target.md`:

   ```markdown
   # Deploy Target

   - Stack: <Vercel | Cloudflare Workers | Supabase | systemd on VPS | scheduled job | other>
   - Production URL / endpoint: <url>
   - Project ID / service name: <id>
   - Region(s): <list>
   - Domain (DNS): <domain> via <provider>
   - Database: <Supabase project / Postgres host / none>
   - Secrets backend: <Vercel env / Doppler / 1Password Connect / VPS .env file>
   - Required env vars: <list with brief descriptions, no values>
   - CI/CD: <GitHub Actions / Vercel auto-deploy / manual via CLI>
   - Auto-deploy on push: <enabled | disabled (recommended for AI swarms)>

   ## Rollback procedure
   - Mechanism: <Vercel instant rollback / git revert + redeploy / systemd restart with prior binary / DB snapshot restore>
   - Time-to-rollback target: < N minutes>
   - Rollback runbook (concrete steps): <numbered list>

   ## Smoke test plan
   - Endpoint(s) to hit: <list>
   - Expected response shapes: <briefly>
   - Smoke test runner: <script path or command>
   - Acceptable failure rate: <usually 0; document any tolerated flakes>
   ```

3. Run secrets scan and config audit:

   ```bash
   gitleaks detect --no-banner --redact --report-format json --report-path /tmp/gitleaks.json || true
   # or trufflehog filesystem . --json > /tmp/trufflehog.json

   # Find any literal-looking secrets in the codebase
   grep -RInE '(api[_-]?key|secret|token|password)\s*=\s*["'\''][^"'\'']{16,}' --include="*.ts" --include="*.js" --include="*.py" --include="*.env*" .
   ```

4. Confirm every required env var listed in `00-deploy-target.md` is set on the target (Vercel envs, Cloudflare secrets, Supabase config, VPS systemd EnvironmentFile, etc.).

5. Run a clean local build to confirm the repo builds reproducibly:

   ```bash
   # Adjust to the project's stack
   bun install --frozen-lockfile && bun run build
   # or: pnpm install --frozen-lockfile && pnpm build
   # or: cargo build --release
   # or: <project-specific>
   ```

6. If the project has DB migrations, confirm:

   * the next-to-run migrations are reversible,
   * the migrations have been tested against a copy of prod data (or against a representative seed),
   * the rollback script for the migration is documented in `00-deploy-target.md`.

7. Run **Random Exploration** one more time with fresh eyes against the deploy-sensitive files (deploy config, env handling, build scripts, migration files). The exact prompt — byte-identical to the Phase 3-4 library — is:

   ```text
   I want you to sort of randomly explore the code files in this project, choosing code files to deeply investigate and understand and trace their functionality and execution flows through the related code files which they import or which they are imported by.

   Once you understand the purpose of the code in the larger context of the workflows, I want you to do a super careful, methodical, and critical check with "fresh eyes" to find any obvious bugs, problems, errors, issues, silly mistakes, etc. and then systematically and meticulously and intelligently correct them.

   Be sure to comply with ALL rules in AGENTS dot md and ensure that any code you write or revise conforms to the best practice guides referenced in the AGENTS dot md file. Use ultrathink.
   ```

   Bias the agent toward deploy/config/migration files via a follow-up bullet, but the *prompt itself* stays unchanged.

8. Run the **Deploy Preflight** prompt `[COMPOSED]`:

   ```text
   We are about to do an initial production deploy. Before I run the deploy command, I want you to carefully audit the codebase for production-readiness issues that wouldn't show up in dev. Specifically:

   - Confirm every environment variable referenced in the code is documented in AGENTS dot md and provisioned in the deploy target.
   - Confirm no secret, API key, token, password, or credential is hardcoded in the repo, including in test files, fixtures, comments, and example configs.
   - Confirm the build runs cleanly from a fresh checkout with no developer-machine-specific paths or assumptions.
   - Confirm any database migrations are reversible and the rollback procedure is documented.
   - Confirm any third-party services (Stripe, Supabase, OpenAI, etc.) the production environment will call are reachable from the production host and authenticated correctly.
   - Confirm the smoke test plan in `.flywheel/phase-5/00-deploy-target.md` is concrete enough to detect a broken deploy.
   - Confirm the rollback runbook in the same file is concrete enough that a tired operator could execute it at 2 a.m.

   Report findings as a checklist. For any item that is not yet satisfied, propose the smallest concrete fix and create a bead for it. Don't deploy yet. Use ultrathink.
   ```

9. Capture results to `01-preflight.md`:

   ```markdown
   # Deploy Preflight — <timestamp>

   ## Repo state
   - HEAD: <commit hash>
   - Branch: <branch>
   - Clean: yes / no

   ## Secrets scan
   - Tool: <gitleaks / trufflehog>
   - Findings: <count>; <details if any>

   ## Env var coverage
   - Required: <count>
   - Set on target: <count>
   - Missing: <list>

   ## Clean build
   - Status: success / failure
   - Build time: <duration>

   ## Migrations
   - New migrations to run: <count>
   - Reversible: yes / no
   - Tested against prod-shape data: yes / no

   ## Random Exploration result
   - Issues found: <count>
   - Issues fixed: <count>
   - Remaining: <count>

   ## Deploy Preflight prompt result
   - Checklist items satisfied: <N>/<M>
   - New beads created: <list of ids>
   - Recommendation: <proceed | block until fixes>
   ```

### A1 quality gates

Do not proceed to A2 until:

1. All preflight checklist items are satisfied **or** explicitly waived by the user with a recorded reason.
2. No hardcoded secrets in the repo.
3. All required env vars are provisioned on the target.
4. The clean build succeeds.
5. The rollback runbook is concrete.

---

## Segment A2 — Provision the Deploy Target (first deploy only)

### A2 goal

Make sure the deploy target itself is configured the way AGENTS.md says it should be. Skip this segment for re-deploys to an unchanged target.

### Procedure

Concrete steps depend on the stack. Document each step taken in `02-deploy-runs/deploy-001-<timestamp>/provision.log`.

For Vercel-style web apps:

```bash
# Link the local project to the Vercel project
vercel link --yes --project <project-name>

# Set production env vars (one per call; see Vercel docs)
vercel env add <NAME> production

# Verify env vars
vercel env ls production

# CRITICAL: disable auto-deploy-on-push if AI agents will be touching the
# repo regularly. Auto-deploy + agent commits = burned credits and
# uncontrolled prod changes.
curl -X PATCH "https://api.vercel.com/v9/projects/${PROJECT_ID}?teamId=${TEAM_ID}" \
  -H "Authorization: Bearer ${VERCEL_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"gitProviderOptions": {"createDeployments": "disabled"}}'
```

For Cloudflare Workers:

```bash
wrangler whoami
wrangler secret put <NAME> --name <worker-name>
```

For Supabase:

```bash
supabase link --project-ref <ref>
supabase db push    # apply migrations to remote
```

For VPS systemd:

```bash
# Copy unit file, enable, but do NOT start yet
sudo systemctl daemon-reload
sudo systemctl enable <service-name>.service
```

For scheduled job pipelines (research-job-style scheduled pipelines):

```bash
# Install the cron / systemd timer / k8s CronJob etc.
# Do NOT enable until A3-A4 are clean.
```

### A2 quality gates

Do not proceed to A3 until:

1. The target is linked / configured.
2. Auto-deploy on push is **disabled** if AI agents are operating on the repo (this is the canonical recommendation — agent commits + auto-deploy is a known credit-burn pattern).
3. Secrets/env vars are present on the target and verified via the target's CLI.

---

## Segment A3 — First Production Deploy

### A3 goal

Push the steady-state codebase to production using the canonical commit-and-deploy discipline.

### Procedure

1. Pick one agent (typically the Claude Code agent with most context) for the deploy work. Do not parallelize the deploy.

2. Send the **canonical Commit Changes** prompt — byte-identical to the Phase 3-4 library — first, even if the repo seems clean. The prompt is intentionally idempotent:

   ```text
   Now, based on your knowledge of the project, commit all changed files now in a series of logically connected groupings with super detailed commit messages for each and then push. Take your time to do it right. Don't edit the code at all. Don't commit obviously ephemeral files. Use ultrathink.
   ```

3. Confirm the push succeeded. Capture HEAD:

   ```bash
   git rev-parse HEAD > .flywheel/phase-5/02-deploy-runs/deploy-001-<timestamp>/git-head.txt
   ```

4. Run the **Production Deploy** prompt `[COMPOSED]`:

   ```text
   We are now ready to deploy to production. The deploy target is documented in `.flywheel/phase-5/00-deploy-target.md`. Specifically:

   - Use the deploy CLI named in that file (vercel / wrangler / supabase / systemd / cron / etc.).
   - Deploy the current main branch HEAD, which I have just committed and pushed.
   - Do not edit application code during this step. If a deploy-time configuration tweak is required, edit only the relevant config file and commit it as a separate, clearly-labelled config commit before redeploying.
   - DCG and SLB are active. If either blocks a command, stop and surface the block to the operator with the full error — do not try to work around it.
   - Capture verbatim deploy output to `.flywheel/phase-5/02-deploy-runs/deploy-001-<timestamp>/deploy.log`.

   After the deploy command returns success, do not assume the system is healthy. Wait for the deploy target to report ready (e.g., Vercel deployment status = READY, systemd unit active, etc.) and then stop. The smoke tests are a separate step. Use ultrathink.
   ```

5. Watch the deploy. Capture the verbatim output to `deploy.log`. If DCG or SLB blocks, surface to the user — do not silently bypass.

6. Once the target reports ready, write `02-deploy-runs/deploy-001-<timestamp>/outcome.md` with the deploy URL, the HEAD commit, and the deploy duration. **Outcome is "deployed; not yet validated" until smoke tests run.**

### A3 quality gates

Do not proceed to A4 until:

1. The deploy CLI returned success.
2. The target reports the deployment as ready / active.
3. `deploy.log` is captured.
4. No DCG/SLB block was bypassed.

---

## Segment A4 — Smoke Tests + Rollback Rehearsal

### A4 goal

Validate that the deploy actually works, and rehearse the rollback path before a real failure forces it.

### Procedure

**Smoke tests:**

1. Run the smoke test suite documented in `00-deploy-target.md`. Capture verbatim output to `smoke-tests.log`.

2. If smoke tests fail, do **not** retry blindly. Investigate the first failure. Common causes: env var missing on target, DNS not propagated, third-party service unreachable from prod, migration not applied. Decide between fix-forward (small config tweak, redeploy) and rollback.

**Rollback rehearsal (first deploy only):**

1. With the user's explicit consent, intentionally trigger the rollback procedure documented in `00-deploy-target.md`. The point is to verify that the runbook is correct *before* a real incident demands it.

2. Concrete examples:

   * Vercel: promote the previous deployment via the UI or CLI; verify production URL serves the previous build; then promote the current deployment back.
   * systemd: `systemctl stop <service>`; `systemctl start <service-prev>`; verify; then restore current.
   * git revert + redeploy: revert the merge commit on a scratch branch; deploy from that branch to a preview / staging slot; verify; do not promote.

3. Capture the rehearsal verbatim to `rollback-rehearsal.log`.

4. If the rehearsal exposes that the rollback procedure does **not** work as documented, that is a Phase 5 STOP-THE-LINE event. Do not proceed to autopilot until the rollback is fixed and re-rehearsed.

5. Update `outcome.md`:

   ```markdown
   # Deploy 001 — <timestamp>

   - HEAD deployed: <commit>
   - Target ready: <timestamp>
   - Smoke tests: passed / failed (<details>)
   - Rollback rehearsed: yes / no
   - Rollback verified working: yes / no
   - Net status: production-ready / production-blocked

   ## Notes
   <anything operator-relevant>
   ```

### A4 quality gates

Do not proceed to A5 until:

1. Smoke tests pass (or any failures are explicitly understood and the user has decided to live with them).
2. The rollback procedure is verified to work end-to-end (first deploy only — subsequent deploys may skip rehearsal, but the user is responsible for re-rehearsing periodically).

---

## Segment A5 — Configure the Ongoing Pipeline

### A5 goal

Wire up the recurring side of Phase 5: scheduled triggers, monitoring, and the autopilot rhythm. After this segment, Track A is done and Track B is ready to start.

### Procedure

1. Pick the autopilot trigger mechanism:

   ```text
   - cron on the VPS (simple, durable)
   - systemd timer (more observable than cron)
   - Claude Code Routines (cloud-hosted, no VPS needed for the trigger)
   - Manual (the user runs it themselves; valid for low-frequency projects)
   ```

2. For cron / systemd timer on the VPS, install the autopilot script:

   ```bash
   # Example cron entry: weekday mornings at 8 AM local
   # 0 8 * * 1-5 /usr/local/bin/flywheel-autopilot <project-name>
   ```

3. For Claude Code Routines, create the routine pointed at the repo with the morning prompt (see Track B below) and the relevant connectors enabled.

4. Set up monitoring appropriate to the stack:

   * Vercel: deployment status webhooks → Slack / Discord / email.
   * VPS service: `systemd` `OnFailure=` hooks; or a small uptime monitor.
   * Supabase: log alerts.
   * For everything: a scheduled `bv --robot-insights | jq '.bottlenecks'` that pings the operator if the bead graph stops moving.

5. Update `REPORT_FINAL.md` to reflect that Track A is complete.

### A5 quality gates

Do not proceed to Track B until:

1. The autopilot trigger is installed and tested (a dry-run executes correctly).
2. Monitoring is in place for both deploy health and swarm health.
3. The operator knows where alerts will land.

---

# Track B — Daily Maintenance (Autopilot Mode)

## Track B framing

Track B is a recurring rhythm with a daily cadence and a weekly cadence. Each day:

```text
Morning:  ru sync + ntm spawn + morning autopilot prompt + brief operator presence check
Midday:   one quick operator check (5-10 min): bv triage, agent mail, stuck beads
Evening:  ru agent-sweep to commit dirty repos with AI-generated messages
```

Each week:

```text
Weekly review: bead progression, autopilot health, drift detection, decision log update
```

The operator's job in Track B is *deliberately small*. The temptation is to over-attend, which both burns the operator's energy and over-corrects the swarm. Two real check-ins per day (morning kickoff + midday glance) is the canonical cadence.

---

## Segment B1 — Morning Autopilot Routine

### B1 goal

Each morning, bring every project up to date, spawn agents across the fleet, point them at the right work via the canonical morning prompt, and capture the day's run folder.

### Procedure

1. Create today's run folder:

   ```bash
   TODAY=$(date -u +%Y-%m-%d)
   mkdir -p .flywheel/phase-5/03-autopilot/runs/$TODAY
   ```

2. Run RU sync across the fleet. The canonical command (from agent-flywheel.com testimonials) is:

   ```bash
   ru sync -j4 | tee .flywheel/phase-5/03-autopilot/runs/$TODAY/ru-sync.log
   ```

   `-j4` runs four parallel sync workers; adjust to fleet size. For a single-project setup, `ru sync` (no `-j`) is fine.

3. Spawn the swarm via NTM. For a single project:

   ```bash
   ntm spawn <project-name> --cc=2 --cod=1 2>&1 | tee .flywheel/phase-5/03-autopilot/runs/$TODAY/ntm-spawn.log
   ```

   For a fleet, repeat per project, or use a wrapper that spawns across the tree. Stagger spawns by 30s as in Phase 3-4.

4. Send the **Morning Autopilot** prompt `[COMPOSED]` to all agents. Save it byte-identically to `morning-prompt-sent.txt`:

   ```text
   Good morning. Before starting any new work today, do the following in order:

   1. Reread AGENTS dot md so it's still fresh in your mind.
   2. Register with MCP Agent Mail and check your inbox; respond promptly to any pending threads from your fellow agents.
   3. Use bv with the robot flags (see AGENTS dot md) to find the most impactful bead(s) ready to work on now. Prefer beads that close out yesterday's in-progress work over starting brand new work.
   4. Pick the next bead you can usefully work on now and start coding on it immediately. Communicate what you're working on to your fellow agents and mark beads appropriately as you work.
   5. Don't get stuck in "communication purgatory" — be proactive about starting tasks that need to be done, but inform your fellow agents via messages when you do so.
   6. If you encounter a bug or issue that goes beyond the current bead, do not silently fix it; create a new bead for it with detailed comments so the rest of the swarm knows it exists.
   7. Respect DCG and SLB. If either blocks a command, do not work around it — surface the block via Agent Mail and continue with a different bead.

   Use ultrathink.
   ```

   Send via `ntm send <project-name> --all "$(cat .flywheel/phase-5/03-autopilot/runs/$TODAY/morning-prompt-sent.txt)"`.

5. Verify that within ~5 minutes each agent has registered with Agent Mail and started picking up beads. If an agent fails to register, the prompt did not land — re-send to that agent.

6. Stop the active operator role. The swarm is now running on its own until midday check-in.

### B1 quality gates

Do not consider B1 complete until:

1. `ru sync` returned success (or the user explicitly accepted partial sync — e.g., if one repo had a merge conflict).
2. Every agent in the swarm registered with Agent Mail.
3. The morning prompt was sent to every agent.
4. At least one bead has moved from `open` → `in_progress` within 10 minutes of the morning prompt.

---

## Segment B2 — Operator Presence (Lightweight)

### B2 goal

A *small* midday and end-of-day presence so the swarm doesn't drift undetected. The biggest mistake is over-management; the second-biggest is forgetting to check at all.

### Midday check (5-10 minutes)

Append to `operator-checkins.md`:

```bash
date -u
bv --robot-triage
br list --status=in_progress
am inbox --unread   # or whatever AM inbox command
git -C <project> log --oneline -10
```

Look for:

* **Stuck beads.** `in_progress` with no recent activity (>30 min). Send the canonical **Move to Next Bead** prompt to the owning agent.
* **Communication purgatory.** Threads with messages but no commits. Send the canonical **Move to Next Bead** to break the deadlock.
* **Compaction signals.** Generic-sounding agent responses. Send the canonical **Post-Compaction** prompt:

  ```text
  Reread AGENTS dot md so it's still fresh in your mind. Use ultrathink.
  ```

* **DCG/SLB blocks waiting on operator approval.** Triage them: approve, reject with explanation, or ask the swarm for more context.
* **Unexpected production alerts.** If monitoring fired, treat it as a Phase 5 incident, not an autopilot blip — see the incident escalation guidance below.

Append a 1-3 line entry per check to `operator-checkins.md`. The log is the proof you actually checked.

### B2 quality gates

There is no hard gate; this segment is continuous through the day. The "fail" condition is a long stretch with no operator entries — that suggests autopilot has been running unattended longer than the operator promised.

---

## Segment B3 — End-of-Day Wrap (`ru agent-sweep`)

### B3 goal

Commit the day's swarm work cleanly across the fleet using `ru agent-sweep` with AI-generated commit messages, then update the day's summary.

### Procedure

1. Run agent-sweep across the fleet. The canonical pattern:

   ```bash
   ru agent-sweep --concurrency 4 2>&1 | tee .flywheel/phase-5/03-autopilot/runs/$TODAY/eod-sweep.log
   ```

   Agent-sweep:

   * discovers dirty repos in the tracked tree,
   * for each, claims the repo via Agent Mail file reservation,
   * spawns an isolated Claude Code session in a worktree,
   * generates commit messages,
   * commits and pushes,
   * releases the reservation.

   No two sweep workers will touch the same repo because of the Agent Mail reservation system.

2. If `ru agent-sweep` is not available or the user prefers single-project flow, send the **canonical Commit Changes** prompt — byte-identical to the Phase 3-4 library — to one agent:

   ```text
   Now, based on your knowledge of the project, commit all changed files now in a series of logically connected groupings with super detailed commit messages for each and then push. Take your time to do it right. Don't edit the code at all. Don't commit obviously ephemeral files. Use ultrathink.
   ```

3. After the sweep, run `git log --oneline -20` per project and append summaries to `day-summary.md`:

   ```markdown
   # Autopilot day summary — <date>

   ## Fleet
   - Projects synced: <N>
   - Projects with new commits today: <M>

   ## Beads
   - Closed today: <count>
   - Opened today: <count> (from autopilot itself, e.g. operator interventions surfaced new work)
   - Net open: <delta>

   ## Production deploys today
   - <count> (most autopilot days will have 0; that is normal)

   ## Operator interventions
   - <count of midday entries>

   ## Anything notable
   - <free-form>
   ```

4. Optionally trigger a deploy if the day's commits represent a deployable increment AND the user has approved auto-deploy from autopilot. **By default, autopilot does not deploy to production.** Promotion to prod is a deliberate operator action that re-enters Track A at A3.

### B3 quality gates

Do not consider the day complete until:

1. `eod-sweep.log` is captured.
2. `git status --porcelain` is clean for every project (or any remaining dirty state is logged as intentional).
3. `day-summary.md` is written.

---

## Segment B4 — Weekly Review

### B4 goal

A 30-60 minute weekly checkpoint that protects against silent autopilot drift. Without this, the swarm will eventually be working on stuff the user no longer cares about, or doing things the user wouldn't approve of in real time.

### Procedure

Once per week (typically the same weekday — say, Monday morning before the day's autopilot run), do the following and write `03-autopilot/weekly/<YYYY-Www>-review.md`:

1. **Bead graph health.**

   ```bash
   bv --robot-triage
   bv --robot-insights | jq '.Cycles, .bottlenecks'
   br list --status=open --age=">7d"   # beads opened more than a week ago and still open
   ```

   Old open beads are smell. Either close them (decision: not doing this), demote them (post-MVP), or actually work them this week.

2. **Production health.** Pull deploy success rate, rollback count, error rate, and uptime from monitoring for the week. Note any incident on `04-incidents.md`.

3. **Autopilot drift detection.** Skim the week's `day-summary.md` files. Are the swarm's accomplishments aligned with the project's goals from `PLAN_FINAL.md`? If the week's work has drifted from the plan, decide:

   * accept the drift and update `PLAN_FINAL.md`,
   * or correct the drift by adjusting the bead graph,
   * or pause autopilot for the week and run a Phase 1 mini-cycle to re-plan.

4. **Cost.** Tokens, deploy credits, third-party API spend. Compare to the prior week.

5. **What surprised you this week.** Free-form. The single most useful prompt for catching drift is "what surprised me this week" — it surfaces things the rolled-up metrics hide.

6. Update `REPORT_FINAL.md` with the latest health summary.

### B4 quality gates

The weekly review is the gate. If two consecutive weekly reviews are skipped, autopilot is running blind — the operator must either restart the rhythm or pause autopilot until they can sustain the cadence.

---

## Segment B5 — When to Escalate from Autopilot to a Real Phase Cycle

Autopilot is for keeping a known-good system moving. It is not for major changes. When any of the following is true, **pause autopilot and re-enter the relevant earlier phase**:

* The plan has materially changed → re-run `flywheel-ideation-planning` (Phase 1).
* New scope requires a different bead structure → re-run `flywheel-decompose-into-beads` (Phase 2).
* The codebase has accumulated enough new work that a focused review pass is needed → re-run `flywheel-swarm-implementation-and-polish` (Phases 3-4) for the new slice.
* A production incident exposes a structural problem → handle the incident first, then re-enter the relevant phase to address the underlying issue.

The skill's job at these moments is to stop autopilot cleanly:

```bash
# Pause cron / systemd timer / Claude Code Routine
# Drain any in-flight bead work to a safe checkpoint
# Have the swarm commit and exit gracefully
ntm send <project-name> --all "Please finish the bead you are currently working on, commit your work, and then go idle. Do not pick up a new bead. Use ultrathink."
# Wait for swarm to drain
ntm kill <project-name> --all
```

Then resume the appropriate earlier-phase skill.

---

# Global quality gates

Phase 5 is healthy when:

* Track A's first deploy completed cleanly with rehearsed rollback.
* `02-deploy-runs/` shows successful deploys with smoke tests passing.
* Track B's `03-autopilot/runs/` shows daily folders with `morning-prompt-sent.txt`, `operator-checkins.md`, and `day-summary.md` populated.
* Weekly reviews exist and are not more than 7 days stale.
* `04-incidents.md` is current — every alert that fired has an entry.
* `05-rollbacks.md` is current — every production rollback has an entry, even rehearsals.
* `REPORT_FINAL.md` reflects the latest state.

---

# Failure modes and recovery

## Deploy succeeds, smoke tests fail

Most common cause: env var or config drift between dev and prod. Do **not** retry deploy blindly. Investigate the first failing smoke test, fix the root cause (env var, DNS, third-party auth, migration), commit the fix, redeploy. If the fix is non-trivial, roll back to the previous deployment and treat this as an incident, not a deploy.

## Deploy succeeds, real users report breakage that smoke tests didn't catch

The smoke tests were too narrow. Roll back. Add a smoke test that would have caught this. Re-deploy. Update `00-deploy-target.md` to expand the smoke plan.

## Rollback rehearsal fails

STOP-THE-LINE event. The rollback runbook is wrong, which means the production deploy is unsafe even though it succeeded. Roll back, fix the runbook, re-rehearse, then redeploy.

## DCG blocks a deploy command

DCG is working correctly. Read the DCG output, understand why the command was deemed dangerous, rephrase the operation, and proceed. Do not bypass DCG. If the DCG rule is wrong for this context, update the DCG ruleset in a separate change.

## SLB asks for two-person approval mid-deploy

Approve only after reading the proposed operation in full. The two-person rule exists because this is the moment where mistakes are catastrophic. If the operation is not what you expect, reject and have the swarm explain.

## Autopilot morning prompt does not land on an agent

Agent Mail registration silence within 5 minutes is the signal. Re-send the morning prompt to that specific agent. If still silent, kill and respawn.

## Agents drift from the plan during autopilot

Caught at the weekly review. Either update the plan to match (the drift was good), correct the bead graph (the drift was random), or pause autopilot and re-plan (the drift indicates a deeper misalignment).

## `ru sync` fails on one repo

Note the failure in `ru-sync.log`, skip that repo for the day's autopilot, and surface it to the operator at midday check. Common causes: merge conflict from human-side commits, repo permissions changed, network blip.

## `ru agent-sweep` produces a bad commit message

The user can amend it. The commit message generation is best-effort. If a particular project consistently produces bad sweep messages, that's a signal to add an example/template to AGENTS.md.

## Production incident during autopilot

Stop autopilot first. Roll back if rollback is the right move (it usually is for real user-facing breakage). Investigate after the user-impact is contained, not before. Append to `04-incidents.md` with a post-mortem within 48 hours.

## Cost runs higher than expected

The weekly review surfaces it. Common causes: a runaway agent in compaction loop, an autopilot that started touching code paths that re-trigger expensive third-party APIs, or a Vercel preview-deploy storm. Pause autopilot, identify the cause, fix, resume.

## User asks to disable autopilot temporarily

Pause the trigger (cron / systemd timer / Routine), drain in-flight work via the graceful-stop pattern in B5, and write the pause reason to `REPORT_FINAL.md` so it doesn't get forgotten. Resuming is a deliberate decision, not a default.

## User asks to disable autopilot permanently / sunset the project

Pause and drain as above, archive `.flywheel/phase-5/`, write a final entry in `REPORT_FINAL.md`, and disable any monitoring / scheduled tasks tied to the project. Note in `00-deploy-target.md` whether the production deployment is being kept (read-only mode) or torn down.

---

# Harness implementation notes

## For Hermes (primary target)

* Hermes drives both tracks from outside the agent sessions.
* For Track A, Hermes runs deploy CLIs directly and captures structured output.
* For Track B, Hermes triggers `ru sync`, `ntm spawn`, and `ntm send` on the daily cadence; the cadence itself can be cron / systemd / Hermes's own scheduler.
* Persist deploy state (most recent successful deploy hash, rollback target, monitoring URLs) in Hermes's per-project state.
* Surface DCG/SLB blocks to the user as first-class events, not buried in logs.

## For Claude Code Routines (autopilot trigger)

* The morning prompt fits cleanly into a Routine. Pin the routine to the relevant repo, attach the connectors the swarm needs (GitHub, Slack/Discord for Agent Mail bridging if applicable), and schedule for the user's local morning.
* Routines run as the user's identity. Commits will appear under the user's GitHub account; that's expected.
* Routines have a daily run cap. If the cap is hit, additional triggers are rejected — surface this to the user rather than retrying silently.

## For OpenClaw / generic skill harnesses

* If the harness has its own scheduler, use it for the autopilot cadence in place of cron.
* If the harness cannot run multiple deploy CLIs, restrict the skill to a single deploy stack and document the constraint in `00-deploy-target.md`.

## For chat-only workflows

* Phase 5 is awkward without a VPS but possible for small projects.
* The user becomes the de-facto cron: they run the morning routine themselves each day, paste outputs back to the chat, and treat the chat as the operator dashboard.
* All artifacts under `.flywheel/phase-5/` are still maintained, just by hand.
* Note the substitution prominently in `00-deploy-target.md`.

## Installation notes

Hermes-style directory example:

```bash
mkdir -p ~/.hermes/skills/ai-agents/flywheel-deploy-and-maintenance
cp SKILL.md ~/.hermes/skills/ai-agents/flywheel-deploy-and-maintenance/SKILL.md
```

OpenClaw-style directory example:

```bash
mkdir -p ~/.openclaw/skills/flywheel-deploy-and-maintenance
cp SKILL.md ~/.openclaw/skills/flywheel-deploy-and-maintenance/SKILL.md
```

Workspace-local example:

```bash
mkdir -p ./skills/flywheel-deploy-and-maintenance
cp SKILL.md ./skills/flywheel-deploy-and-maintenance/SKILL.md
```

Intended slash commands:

```text
/flywheel-deploy-and-maintenance
/flywheel-phase-5
/autopilot
```
