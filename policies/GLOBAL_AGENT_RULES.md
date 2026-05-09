# Global Agent Rules

These rules apply to every agent (Claude Code, Codex, Gemini CLI) in every session.

## Always
- Read PROJECT_BRIEF.md, ARCHITECTURE.md, TESTING.md, SECURITY.md, and CURRENT_STATE.md before coding.
- Work on one task at a time.
- Use the assigned branch and worktree.
- Keep diffs small.
- Run tests before final report.
- Update CURRENT_STATE.md when behavior changes.
- Reserve files via Agent Mail before editing (advisory; worktrees are the real protection).

## Never without explicit approval
- sudo
- rm -rf
- git reset --hard
- git clean -fd
- push to main
- force push
- deploy production
- edit .env or read production secrets
- change DNS
- delete database data
- modify billing
- send external emails
- access personal accounts
- install unknown packages
- curl ... | sh  /  wget ... | sh

## Reporting
- Every task ends with a status report: what was done, what was tested, what was skipped, what's risky.
- Surface uncertainty rather than guessing.
