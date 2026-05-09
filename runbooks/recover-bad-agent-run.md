# Recover Bad Agent Run

## When to use this runbook

An agent has produced unexpected, broken, or unsafe output. The task needs to be unwound and either retried or abandoned.

## Triage first

Answer these before doing anything destructive:

1. Did the agent push to a remote branch? (check `git log --all --remotes`)
2. Did the agent modify files outside its worktree? (`find ~/dev -newer <task-start-time>`)
3. Did the agent run any commands requiring approval that weren't approved?
4. Are there any uncommitted changes worth preserving for inspection?

## Steps

### If contained to the worktree (no push, no out-of-bounds writes)

1. Save the agent's transcript and any artifacts to ~/dev/agent-memory/incidents/INC-YYYY-MM-DD/.
2. Capture diff for postmortem:
cd ~/dev/worktrees/<project>-BR-XXX
git diff main > ~/dev/agent-memory/incidents/INC-YYYY-MM-DD/diff.patch
3. Remove worktree:
cd ~/dev/repos/<project>
git worktree remove --force ~/dev/worktrees/<project>-BR-XXX
git branch -D br-XXX-<slug>
4. Mark br task as failed; do not retry until root cause is known.

### If a remote branch was created

1. Do NOT delete the remote branch yet — it's evidence.
2. Capture full state to incident folder.
3. Decide: rerun task with stricter constraints, or abandon and rewrite the bead.

### If files outside the worktree were modified

1. Stop the agent immediately (`flywheel-killall` if needed).
2. Identify changed files: `find ~/dev -newer <timestamp> -type f`.
3. Restore from git or backup as appropriate.
4. Treat as a security incident; write INCIDENT_REPORT.md.
5. Tighten policies before any retry.

## Verification

- No stray branches or worktrees remain
- CURRENT_STATE.md notes the failed task
- Incident folder has full transcript + diff
- Lessons captured in retrospective skill output

## Common failures

(Fill in as encountered.)
