# Start New Project

## When to use this runbook

Initializing a new project repo to plug into the agent stack.
Run this any time you create a new project from scratch.

## Prerequisites

- agent-operating-system is up to date locally (`git -C ~/dev/repos/agent-operating-system pull`)
- GitHub auth is working (`gh auth status`)
- `project-init` script is in PATH (`which project-init`)

## Steps

### 1. Create the GitHub repo

```bash
gh repo create <project-name> --private
```

### 2. Clone to the canonical location

```bash
cd ~/dev/repos
gh repo clone <project-name>
```

### 3. Run project-init

```bash
project-init <project-name>
```

This copies all 10 standard memory files from templates/, creates .gitignore,
creates a CI skeleton, and makes an initial commit.

The 10 files it creates:
  AGENTS.md         — rules of engagement for every agent
  PROJECT_BRIEF.md  — what the project is and why (stable)
  ARCHITECTURE.md   — technical map (stable)
  CURRENT_STATE.md  — live state, updated every session (rapidly changing)
  DECISIONS.md      — ADR log, append-only (grows over time)
  TESTING.md        — how to validate work (stable)
  SECURITY.md       — threat model and secrets protocol (stable)
  DEPLOYMENT.md     — where it runs and how to ship (stable)
  BUGS.md           — known deferred issues (grows over time)
  CHANGELOG.md      — release history (grows over time)

### 4. Fill in the memory files (in priority order)

Fill these in before running any agent on the project:

1. PROJECT_BRIEF.md  — what the project is, who it's for, success criteria, non-goals
2. ARCHITECTURE.md   — components, data flow, storage, external services
3. AGENTS.md         — fill in the PROJECT-SPECIFIC RULES section (stack, test command, etc.)
4. TESTING.md        — fill in the EXACT test command and test layout
5. SECURITY.md       — what data is sensitive, the threat model
6. DEPLOYMENT.md     — where it runs, how to deploy, rollback procedure
7. CURRENT_STATE.md  — update "Next recommended action" to the first real task

These files are load-bearing. Agents will fail to do good work without them.
Filling them in IS the planning act — they force you to think through the project
before the first line of code.

DECISIONS.md, BUGS.md, and CHANGELOG.md start essentially empty and fill in
over time.

### 5. Set branch protection on main

GitHub Settings > Branches > Add rule:
- Branch name: main
- Require PR before merging: yes
- Require status checks to pass: yes (add your CI check name)
- Do not allow force pushes: yes

### 6. Push and verify CI

```bash
cd ~/dev/repos/<project-name>
git push origin main
```

Create a test PR to confirm CI runs.

### 7. Enable the flywheel

If using the Flywheel workflow:
- Run `/flywheel-ideate` (skill 1) to produce PLAN_FINAL.md
- Run `/flywheel-decompose` (skill 2) to produce initial task beads

If using the simpler worktree stack:
- Run `wt-new <project-name> <first-task-id>` to create the first task branch
- Dispatch agent with the worktree path in context

## Verification checklist

- [ ] Repo visible on GitHub
- [ ] All 10 memory files present in repo root
- [ ] PROJECT_BRIEF.md filled in (not just placeholders)
- [ ] ARCHITECTURE.md filled in (not just placeholders)
- [ ] AGENTS.md project-specific section filled in
- [ ] TESTING.md has a working test command
- [ ] .gitignore includes .env
- [ ] Branch protection enabled on main
- [ ] CI workflow runs on a test PR
- [ ] CURRENT_STATE.md has a meaningful "Next recommended action"

## Common failures

- project-init says "not a git repo": clone the repo first, then run project-init
- CI fails immediately: the ci.yml skeleton needs the test command filled in
- Agent ignores memory files: confirm AGENTS.md is in the repo ROOT (not a subdir)
- CURRENT_STATE.md gets stale: enforce the end-of-session ritual in AGENTS.md
