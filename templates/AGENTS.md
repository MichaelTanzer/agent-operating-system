# AGENTS.md
#
# This is the CONSTITUTION for every agent working on this project.
# Copy verbatim into every new project repo root. Fill in the PROJECT-SPECIFIC
# sections. The GLOBAL sections are non-negotiable.

## Project identity

Project:  <!-- PROJECT NAME -->
Repo:     <!-- github.com/ORG/REPO -->
Owner:    <!-- @github-handle -->
Updated:  <!-- YYYY-MM-DD -->

---

## GLOBAL RULES — every agent, every session, no exceptions

### Step 0: Orient before you touch anything

Read these files, in this order, at the start of every session:

1. AGENTS.md        (this file — rules of engagement)
2. PROJECT_BRIEF.md (what the project is and why)
3. ARCHITECTURE.md  (the technical map)
4. TESTING.md       (how to validate your work)
5. SECURITY.md      (threat model and red lines)
6. CURRENT_STATE.md (where things stand RIGHT NOW)
7. Your assigned task / bead

Seven reads, ~2,000-5,000 tokens. Do not skip them. Do not substitute with
grep or git log. These files ARE the context.

Read on demand (only when your task touches that area):
- DECISIONS.md   — before changing any architectural pattern
- DEPLOYMENT.md  — before any deploy-related work
- BUGS.md        — before touching any area marked fragile
- CHANGELOG.md   — for historical release context

### Working discipline

- One task = one branch = one worktree = one agent. Stay in your worktree.
- The canonical repo at ~/dev/repos/<SLUG> is READ-ONLY for you.
- Keep diffs small. Many small commits beat one large commit.
- Run the test suite before marking any task done.
- Write a status report at the end of every task:
    What was done | What was tested | What was skipped | What's risky

### Commit messages (Conventional Commits)

  type(scope): short description under 72 chars

  Longer body if needed. Wrap at 72 chars.
  Reference the task/bead ID.

Types: feat  fix  refactor  docs  test  ci  chore  perf

### End-of-session ritual — REQUIRED, non-negotiable

Before ending any session, update CURRENT_STATE.md:

1. Set "Updated:" to today's date
2. Move completed work into "Recently completed"
3. Update "Working" and "Broken" to reflect reality now
4. Update "Risks" with anything new you noticed
5. Set "Next recommended action" to the single clearest next step

This is the handoff document. The next agent reads it first. If you
don't update it, the next session starts blind.

### NEVER without explicit human approval

Operational:
- sudo
- rm -rf  |  git clean -fd  |  git reset --hard
- force push  |  push to main directly
- deploy to production
- enable auto-deploy-on-push (AI agents + auto-deploy = uncontrolled releases)

Data:
- DELETE or TRUNCATE any table
- Edit .env or read production secrets
- Access production databases

Infrastructure:
- Change DNS records
- Modify billing or quotas
- Modify firewall or security group rules

External:
- Send emails, SMS, or notifications to real users
- Make financial transactions
- Post to public social accounts

Packages:
- Install packages not already in requirements/package.json/pyproject.toml
- curl URL | sh  or  wget URL | sh
- Install system packages via apt/brew/yum

If you are uncertain whether something requires approval — STOP and ask.
Surfacing uncertainty is never the wrong move.

---

## PROJECT-SPECIFIC RULES

### Tech stack

<!-- e.g.
Language:  Python 3.12
Framework: FastAPI
Database:  PostgreSQL 16 + pgvector
Frontend:  React 18 + Vite
Infra:     Ubuntu 22.04 VPS, Vercel for frontend
-->

### How to run tests

```bash
# fill in the EXACT command(s) — copy-paste ready
```

### How to run locally

```bash
# fill in the EXACT command(s) — copy-paste ready
```

### File ownership conventions

<!--
Examples:
  src/api/       — HTTP layer only; no business logic
  src/services/  — all business logic lives here
  src/models/    — data shapes, no logic
  tests/         — mirrors src/ structure
-->

### Branch naming

  feat/<slug>       new features
  fix/<slug>        bug fixes
  refactor/<slug>   code restructuring
  docs/<slug>       documentation only
  ci/<slug>         CI/CD changes
  chore/<slug>      deps, tooling, no behavior change

### Required CI gates before merge

<!-- list the checks that must be green before a PR can merge -->
- [ ] tests pass
- [ ] linter/formatter clean
- [ ] (add project-specific checks)

### Secrets handling

- Never hardcode secrets. All secrets via environment variables.
- Allowed secret names live in .env.example only (no values).
- Real .env is gitignored and never committed.
- See SECURITY.md for the full threat model.

### PR rules

- Every PR must include: description, test evidence, CURRENT_STATE.md updated.
- No self-merge. PRs are reviewed by the human owner or a designated review agent.

---

## Agent roster (fill in as tasks are active)

| Agent | Task / Bead ID | Worktree path | Status |
|-------|---------------|---------------|--------|
| —     | —             | —             | —      |

---

## Escalation

Blocked? Uncertain? About to do something irreversible?
STOP. Report. Do not guess. Do not work around the block.
