# Morning briefing configuration

This directory contains the configuration scaffold for the morning briefing system.

## Files

- `jobs.yaml` defines scheduled briefing jobs and delivery defaults.
- Kanban dry-run scripts emit read-only all-board JSON for briefing and cleanup jobs.
- `jobs.schema.json` validates job configuration shape.
- `watchlist.yaml` stores the approved 23-company Watchlist Digest universe, including aliases, tickers, sectors, material topics, query focus, and per-company noise exclusions.
- `source_rubric.yaml` defines source-quality tiers, source scoring, materiality signals, consulting/white-paper query patterns, and low-quality/noise exclusions for the Watchlist Digest agent.

The current delivery default is Discord while dedicated email delivery remains under setup.
