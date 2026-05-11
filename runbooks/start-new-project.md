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

### 4. Bootstrap CI and PR review gates

Copy the reusable GitHub Actions templates into the new project's active
workflow directory, dropping the `.tmpl` suffix:

```bash
cd ~/dev/repos/<project-name>
mkdir -p .github/workflows .github
cp ~/dev/repos/agent-operating-system/templates/.github/workflows/ci.yml.tmpl \
  .github/workflows/ci.yml
cp ~/dev/repos/agent-operating-system/templates/.github/workflows/markdown-lint.yml.tmpl \
  .github/workflows/markdown-lint.yml
cp ~/dev/repos/agent-operating-system/templates/.github/workflows/secret-scan.yml.tmpl \
  .github/workflows/secret-scan.yml
cp ~/dev/repos/agent-operating-system/templates/PULL_REQUEST_TEMPLATE.md \
  .github/PULL_REQUEST_TEMPLATE.md
```

Then add a project-specific `Makefile` with at least:

```make
.PHONY: lint ci

lint:
	# project-specific lint command

ci: lint
	# project-specific tests/build command
```

The generic `ci.yml` workflow intentionally calls `make ci`, so each project can
choose its own language-specific validation without changing the workflow.

For review, use `~/dev/repos/agent-operating-system/policies/CODEX_REVIEW_PROMPT.md`
as the standard Codex reviewer prompt when a Claude-generated branch is ready for
independent review.

### 5. Fill in the memory files (in priority order)

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

### 6. Register safe project memory in Gbrain, if enabled

If Gbrain is installed and the project is allowed by `policies/GBRAIN_POLICY.md`,
add only the approved project-memory artifacts to `~/dev/repos/brain/`:

```bash
mkdir -p ~/dev/repos/brain/projects/<project-name>
cp PLAN_FINAL.md CURRENT_STATE.md DECISIONS.md \
  ~/dev/repos/brain/projects/<project-name>/ 2>/dev/null || true
```

Do not ingest code, emails, calendars, chat exports, browser history, financial
records, or personal documents. Before importing a new source, read:

- `policies/GBRAIN_POLICY.md`
- `runbooks/backup-restore-gbrain.md`
- `runbooks/delete-gbrain-memory.md`

After adding files, run a local import without embeddings unless an embedding
provider is already approved:

```bash
gbrain import ~/dev/repos/brain --no-embed
gbrain search "<project-name>"
```

### 7. Set branch protection on main

GitHub Settings > Branches > Add rule:
- Branch name: main
- Require PR before merging: yes
- Require status checks to pass: yes (add your CI check name)
- Do not allow force pushes: yes

### 8. Push and verify CI

```bash
cd ~/dev/repos/<project-name>
git push origin main
```

Create a test PR to confirm CI runs. A good smoke test is a throwaway branch with
one deliberately malformed Markdown file. Confirm markdown-lint fails for the
expected reason, then close the PR without merging.

### 9. Enable the flywheel

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
- [ ] `.github/workflows/ci.yml` calls `make ci`
- [ ] `.github/workflows/markdown-lint.yml` runs markdownlint on PRs
- [ ] `.github/workflows/secret-scan.yml` runs gitleaks on PRs
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` exists
- [ ] Makefile has `lint` and `ci` targets
- [ ] Branch protection enabled on main
- [ ] CI workflow runs on a test PR
- [ ] CURRENT_STATE.md has a meaningful "Next recommended action"
- [ ] If Gbrain is enabled: only approved project-memory artifacts were imported
- [ ] If Gbrain is enabled: `gbrain search "<project-name>"` returns expected project memory

## Common failures

- project-init says "not a git repo": clone the repo first, then run project-init
- CI fails immediately: the ci.yml skeleton needs the test command filled in
- `make ci` fails in GitHub Actions: ensure your Makefile installs any language tooling first or uses checked-in lockfiles
- markdown-lint flags long prose: tune `.markdownlint.json`; do not disable all rules blindly
- gitleaks flags example tokens: add narrowly-scoped dummy patterns to `.gitleaks.toml`
- Agent ignores memory files: confirm AGENTS.md is in the repo ROOT (not a subdir)
- CURRENT_STATE.md gets stale: enforce the end-of-session ritual in AGENTS.md
