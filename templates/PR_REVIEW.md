# PR Review Checklist

## Acceptance criteria
- [ ] Does this match the task acceptance criteria?
- [ ] Is the scope limited to the stated task?

## Tests
- [ ] Are tests added or updated?
- [ ] Does CI pass?
- [ ] Are edge cases covered?

## Hygiene
- [ ] Did the agent avoid unrelated changes?
- [ ] Were secrets avoided?
- [ ] Were docs updated if behavior changed?
- [ ] Is the diff small enough to review (~400 lines or less)?

## Safety
- [ ] Is rollback obvious?
- [ ] Are migrations reversible?
- [ ] Are there any new external dependencies? If so, are they vetted?

## Architecture
- [ ] Does this match ARCHITECTURE.md?
- [ ] If it diverges, is the divergence documented in DECISIONS.md?

## Reviewer summary

One paragraph: what was changed, why, and any concerns.
