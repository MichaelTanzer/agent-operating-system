# agent-operating-system

Skills, policies, templates, and runbooks for the Flywheel agent stack.

## Layout

- `skills/` — Flywheel skills (each directory contains one SKILL.md)
- `policies/` — Global rules every agent follows
- `templates/` — Starter files copied into new project repos
- `runbooks/` — Operational procedures for incidents and recovery

## Skills

Four consolidated Flywheel phases:

1. `1_Idea_Plan_SKILL/` — Idea → plan
2. `2_Decompose_Into_Beads_SKILL/` — Plan → tasks (beads)
3. `3_Swarm_Implementation_And_Polish_SKILL/` — Tasks → implementation + review
4. `4_Deploy_And_Maintenance_SKILL/` — Merge → deploy → memory

## Consumers

- **Hermes** (primary) — points at `skills/` and loads SKILL.md files at startup
- **Claude Code** — can load skills via symlink into `~/.claude/skills/`
- **Codex / Gemini CLI** — read `policies/` for review and summarization context

## Updating

Edits go through the normal flow: branch → PR → CI → review → merge.
No direct pushes to `main`, even for skill edits.

## Related

- Project memory templates from `templates/` are copied into individual project repos.
- Operational incidents that exercise these runbooks should produce updates back here.
