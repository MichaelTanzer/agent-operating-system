# Morning briefing configuration

This directory contains the configuration scaffold for the morning briefing system.

## Files

- `jobs.yaml` defines scheduled briefing jobs and delivery defaults.
- Kanban dry-run scripts emit read-only all-board JSON for briefing and cleanup jobs.
- `jobs.schema.json` validates job configuration shape.
- `watchlist.yaml` stores the approved company watchlist used by briefing jobs.

The current delivery default is Discord while dedicated email delivery remains under setup.
