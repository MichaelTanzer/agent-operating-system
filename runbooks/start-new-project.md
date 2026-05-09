# Start New Project

## When to use this runbook

Initializing a new project repo to plug into the Flywheel stack.

## Prerequisites

- agent-operating-system is up to date locally
- VPS has latest skills loaded
- GitHub auth is working (`gh auth status`)

## Steps

1. Create repo on GitHub:
cat > start-new-project.md <<'EOF'
# Start New Project

## When to use this runbook

Initializing a new project repo to plug into the Flywheel stack.

## Prerequisites

- agent-operating-system is up to date locally
- VPS has latest skills loaded
- GitHub auth is working (`gh auth status`)

## Steps

1. Create repo on GitHub:
gh repo create <project-name> --private
2. Clone to canonical location:
cd ~/dev/repos
gh repo clone <project-name>
cd <project-name>
3. Copy memory templates from agent-operating-system:
cp ~/dev/repos/agent-operating-system/templates/PROJECT_BRIEF.md .
cp ~/dev/repos/agent-operating-system/templates/ARCHITECTURE.md .
cp ~/dev/repos/agent-operating-system/templates/CURRENT_STATE.md .
4. Add AGENTS.md (copy from policies/GLOBAL_AGENT_RULES.md as starting point).
5. Add .gitignore with .env exclusion.
6. Add basic CI workflow (.github/workflows/ci.yml).
7. Set branch protection on main.
8. Initial commit and push.
9. Run `/flywheel-ideate` (skill 1) to produce PLAN_FINAL.md.
10. Run `/flywheel-decompose` (skill 2) to produce initial br tasks.

## Verification

- Repo visible on GitHub
- Branch protection enabled
- CI workflow runs on a dummy PR
- PLAN_FINAL.md exists
- 5-10 initial br tasks created

## Common failures

(Fill in as encountered.)
