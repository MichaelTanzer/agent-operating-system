# Human Approval Policy

## Auto-approved (agent proceeds alone)
- Reading code in assigned worktree
- Running tests
- Creating commits on a task branch
- Opening a draft PR
- Reading docs and policies

## Requires explicit approval
- Merging to main
- Deleting files outside the worktree
- Installing new top-level dependencies (package.json, requirements.txt, Cargo.toml, etc.)
- Any sudo command
- Production deploy
- Database schema changes
- Modifying CI configuration
- Modifying any file in /etc/, ~/.ssh, or ~/dev/agent-memory/
- Changing branch protection or repo settings
- Adding new GitHub Actions secrets

## Approval format
When requesting approval, agents must state:
- The exact command or change being proposed
- Why it's needed
- What it will affect
- How to undo it
