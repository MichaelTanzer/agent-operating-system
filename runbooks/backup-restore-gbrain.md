# Backup and Restore Gbrain

Updated: 2026-05-11

## Purpose

Back up and restore the Gbrain installation without sending brain data off the
VPS by default. The current stack now uses local PostgreSQL + pgvector, with the
original PGLite brain preserved as a fallback backup.

## Current engine

```text
engine: postgres
database: gbrain
role: gbrain
connection URL file: ~/.gbrain/database_url
legacy PGLite file preserved: ~/.gbrain/brain.pglite
```

Do not print or commit the connection URL. It contains a database password.

## Locations

- Gbrain tool repo: `~/gbrain`
- Brain content repo: `~/dev/repos/brain`
- Gbrain config: `~/.gbrain/config.json`
- Postgres connection URL: `~/.gbrain/database_url` (mode 600)
- Repo backups: `~/dev/backups/brain-repo/*.tar.gz`
- Markdown DB exports: `~/dev/backups/brain-db/*.tar.gz`
- Postgres custom dumps: `~/dev/backups/brain-db/postgres-gbrain-*.dump`
- Logs: `~/dev/logs/gbrain-backup.log`

## Backup policy

- Keep local backups for 30 days.
- For long-term durability, add encrypted off-machine backup later; local VPS
  backups do not protect against disk loss.
- Do not push the brain repo to GitHub or another remote without explicit
  approval and a policy update.
- Do not back up secrets. Brain content must not contain secrets by policy.

## Manual backup

```bash
set -euo pipefail
export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
DATE=$(date +%F-%H%M%S)
mkdir -p "$HOME/dev/backups/brain-repo" "$HOME/dev/backups/brain-db"

# 1. Brain markdown repo snapshot
tar -czf "$HOME/dev/backups/brain-repo/$DATE.tar.gz" \
  -C "$HOME/dev/repos" brain

# 2. Engine-agnostic markdown export snapshot
gbrain export --dir "$HOME/dev/backups/brain-db/$DATE"
tar -czf "$HOME/dev/backups/brain-db/$DATE.tar.gz" \
  -C "$HOME/dev/backups/brain-db" "$DATE"
rm -rf "$HOME/dev/backups/brain-db/$DATE"

# 3. Active Postgres DB custom-format dump
pg_dump -Fc "$(cat "$HOME/.gbrain/database_url")" \
  > "$HOME/dev/backups/brain-db/postgres-gbrain-$DATE.dump"
```

## Daily cron

Installed script:

```text
~/dev/scripts/gbrain-backup.sh
```

Cron:

```cron
17 3 * * * $HOME/dev/scripts/gbrain-backup.sh >> $HOME/dev/logs/gbrain-backup.log 2>&1
```

The script writes:

- repo tarball;
- `gbrain export --dir` markdown export tarball;
- `pg_dump -Fc` dump when active engine is Postgres;
- retention cleanup for files older than 30 days.

## Restore smoke test — markdown export path

This verifies the source/export backup can restore into a scratch directory and
that Gbrain can search after import. It does not overwrite the live brain.

```bash
set -euo pipefail
export PATH="$HOME/.bun/bin:$HOME/.local/bin:$PATH"
DATE=<backup-stamp>
SCRATCH="$HOME/dev/tmp/brain-restore-$DATE"
mkdir -p "$SCRATCH"

tar -xzf "$HOME/dev/backups/brain-repo/$DATE.tar.gz" -C "$SCRATCH"
test -f "$SCRATCH/brain/RESOLVER.md"

gbrain import "$SCRATCH/brain" --no-embed
gbrain search "Phase 11 review gates"
gbrain doctor --json
```

## Full restore — Postgres dump path

Use this if the live Postgres `gbrain` database is corrupted. This is
destructive to the live DB; stop Gbrain daemons first and get explicit approval.

```bash
sudo systemctl stop hermes || true
# stop any future gbrain-ingest service here if created

createdb -T template0 gbrain_restore_test
pg_restore -d gbrain_restore_test ~/dev/backups/brain-db/postgres-gbrain-<DATE>.dump
psql gbrain_restore_test -c 'select count(*) from pages;'
```

For actual live restore, restore into a fresh database first, verify page count
and `gbrain doctor`, then switch `~/.gbrain/database_url` / `~/.gbrain/config.json`
to the restored database. Do not overwrite the only live DB without a verified
restore target.

## Current verification

- 2026-05-11: pre-migration PGLite export and repo tarball created.
- 2026-05-11: migrated to local PostgreSQL 18 + pgvector 0.8.2.
- 2026-05-11: `gbrain doctor` reported:
  - connection OK, 10 pages;
  - pgvector installed;
  - RLS enabled on 36/36 public tables;
  - auto-RLS event trigger installed;
  - schema version 50;
  - embeddings 100% coverage.
- 2026-05-11: Postgres custom dump created and backup script updated.
