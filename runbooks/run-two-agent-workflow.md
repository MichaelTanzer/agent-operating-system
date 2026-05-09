# Run Two-Agent Workflow

## When to use this runbook

Running Claude Code (builder) and Codex (reviewer) in parallel on a single task.
This is the default after Phase 13 swarm-prepare is in place.

## Prerequisites

- One ready br task (no unresolved dependencies)
- Worktree created for the task
- Agent Mail identities configured
- tmux/NTM cockpit running

## Steps

1. Pick the next ready task from `bv`.
2. Create worktree:
cd ~/dev/repos/<project>
git switch main && git pull
git worktree add ~/dev/worktrees/<project>-BR-XXX -b br-XXX-<slug>
3. Open new NTM pane, name it `agent-<project>-br-XXX-builder`.
4. Launch Claude Code in that pane, in plan mode, pointed at the worktree.
5. Claude Code reads PROJECT_BRIEF, ARCHITECTURE, CURRENT_STATE, AGENTS.md, and the bead.
6. Claude Code proposes a plan and waits for approval.
7. Approve plan; Claude Code implements.
8. Claude Code runs tests in the worktree.
9. Claude Code opens a draft PR.
10. Open second NTM pane: `agent-<project>-br-XXX-reviewer`.
11. Launch Codex in that pane, point at the PR diff.
12. Codex runs review using PR_REVIEW.md checklist.
13. If Codex flags issues, route back to Claude Code.
14. When CI passes and Codex approves, mark PR ready for human merge.
15. Human merges via GitHub UI or `gh pr merge`.
16. Run `/flywheel-merge-memory` skill (or whatever you named it).

## Verification

- Branch is merged to main
- br task is closed
- CURRENT_STATE.md is updated
- Worktree is removed: `git worktree remove ~/dev/worktrees/<project>-BR-XXX`

## Common failures

(Fill in as encountered.)
