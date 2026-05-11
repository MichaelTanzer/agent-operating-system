# Testing

Updated: <!-- YYYY-MM-DD -->

## Test command (copy-paste ready)

```bash
# The exact command to run the full test suite from the project root.
# This is what every agent runs before marking a task done.
# Example: pytest tests/ -q
```

## What "done" means for a code change

A PR is not ready to merge until ALL of the following are true:

- [ ] Test command above exits 0
- [ ] No new linter errors (see Linter section below)
- [ ] Any new behavior has a test covering it
- [ ] CURRENT_STATE.md is updated

## Test layout

<!-- Where tests live and how they're organized.
     Example:
     tests/
       unit/       — pure function tests, no I/O
       integration/ — tests that hit the real DB (uses a test DB)
       e2e/        — full HTTP round-trips against a local server
     
     Test file naming: test_<module_name>.py mirrors src/<module_name>.py
-->

## Test database / fixtures

<!-- How to set up the test DB or fixtures before running tests.
     Example:
     pytest --setup-show will run conftest.py which:
     - creates a temp Postgres DB (DATABASE_URL_TEST env var)
     - applies all migrations
     - seeds test data from tests/fixtures/seed.sql
     - tears down after the session
-->

## Linter / formatter

```bash
# The exact lint/format check command.
# Example: ruff check . && ruff format --check .
# Example: npx eslint src/ && npx prettier --check .
```

Auto-fix command (safe to run before committing):
```bash
# Example: ruff format . && ruff check --fix .
```

## Coverage expectations

<!-- What level of coverage is expected, and for which parts.
     Example:
     - Unit tests: aim for > 80% on src/services/ and src/models/
     - Integration tests: every API endpoint has at least one happy-path test
     - No coverage requirement on src/scripts/ (one-off tooling)
-->

## What NOT to test

<!-- Things explicitly out of scope for automated tests.
     Example:
     - Third-party SDK internals (mock at the boundary, don't test the SDK)
     - Visual layout (manual review)
     - LLM output quality (separate eval harness, not pytest)
-->

## CI integration

<!-- How tests run in CI. Which workflow file?
     Example: .github/workflows/ci.yml
     - Triggers on: push to any branch, PR to main
     - Runs: pytest + ruff
     - Required to pass before merge: yes
-->
