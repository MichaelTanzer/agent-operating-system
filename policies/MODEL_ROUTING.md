# Model Routing

## Claude Code

Use for:
- Multi-file implementation
- Refactors
- Feature work
- Local test iteration

## Codex

Use for:
- PR review
- Security review
- Debugging hard failures
- Alternative implementation analysis

Standard review prompt:
- `policies/CODEX_REVIEW_PROMPT.md`

When reviewing a Claude Code branch, Codex must use that prompt as the baseline:
reviewer role only, read linked bead acceptance criteria first, check out the
branch locally, run tests, and return a structured PASS / NEEDS_CHANGES / FAIL
report.

## Gemini CLI

Use for:
- Repo summaries
- Documentation
- Large-context scanning
- Research-style comparison
- Cheap first-pass analysis

## Routing rules

- Never use the same agent as both implementer and reviewer on the same PR.
- Default reviewer for Claude Code branches: Codex.
- Default summarizer for large PRs: Gemini.
- Escalate to a second model if the first produces low-confidence output on a safety-relevant task.
