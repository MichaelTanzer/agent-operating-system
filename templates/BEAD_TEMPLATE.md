# Bead Template

Each task ("bead") in the br/bv system uses this structure.

## ID

BR-XXX

## Title

Short, action-oriented (e.g., "Add CI workflow for unit tests")

## Goal

One sentence on what this task accomplishes and why it matters.

## Acceptance criteria

- [ ] Concrete, testable condition 1
- [ ] Concrete, testable condition 2
- [ ] Concrete, testable condition 3

## Dependencies

- Upstream tasks that must be complete first: BR-XXX, BR-YYY
- External dependencies: API keys, accounts, deployments

## Files likely involved

- path/to/file1
- path/to/file2

## Tests required

- Unit tests for X
- Integration test covering Y

## Agent assignment

- Implementer: claude-builder
- Reviewer: codex-reviewer
- Summarizer (if PR is large): gemini-scout

## Risk level

low | medium | high

## Risk notes

What could go wrong, blast radius, rollback path.

## Estimated diff size

S (<100 lines) | M (100-400) | L (>400, consider splitting)
