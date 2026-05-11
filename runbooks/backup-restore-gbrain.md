# Backup and Restore Gbrain

Updated: 2026-05-11

## Purpose

Back up and restore the Phase 12 Gbrain installation without sending brain data
off the VPS.

## Locations

- Gbrain tool repo: `~/gbrain`
- Brain content repo: `~/dev/repos/brain`
- Brain database: `~/.gbrain/brain.pglite` unless `gbrain doctor --json` reports a
  different path
- Repo backups: `~/dev/backups/brain-repo/YYYY-MM-DD.tar.gz`
- DB exports: `~/dev/backups/brain-db/YYYY-MM-DD/` or `YYYY-MM-DD.tar.gz`
- Logs: `~/dev/logs/gbrain-backup.log`

## Backup policy

- Keep backups local to the VPS.
- Retain the last 30 daily backups.
- Do not push the brain repo to GitHub or another remote without explicit
  approval and a policy update.
- Do not back up secrets. Brain content must not contain secrets by policy.

## Manual backup

```bash
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
DATE=$(date +%F)
mkdir -p "$HOME/dev/backups/brain-repo" "$HOME/dev/backups/brain-db"

# 1. Brain markdown repo snapshot
tar -czf "$HOME/dev/backups/brain-repo/$DATE.tar.gz" \
  -C "$HOME/dev/repos" brain

# 2. Gbrain DB export as markdown snapshot
# Gbrain 0.32 exposes `gbrain export --dir`, not `gbrain export --all`.
rm -rf "$HOME/dev/backups/brain-db/$DATE"
gbrain export --dir "$HOME/dev/backups/brain-db/$DATE"
tar -czf "$HOME/dev/backups/brain-db/$DATE.tar.gz" \
  -C "$HOME/dev/backups/brain-db" "$DATE"
rm -rf "$HOME/dev/backups/brain-db/$DATE"

# 3. Retention: keep 30 newest archives
find "$HOME/dev/backups/brain-repo" -name '*.tar.gz' -type f -mtime +30 -delete
find "$HOME/dev/backups/brain-db" -name '*.tar.gz' -type f -mtime +30 -delete
```

## Daily cron

Install a daily cron after manual backup succeeds:

```bash
mkdir -p "$HOME/dev/scripts" "$HOME/dev/logs"
cat > "$HOME/dev/scripts/gbrain-backup.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
DATE=$(date +%F)
mkdir -p "$HOME/dev/backups/brain-repo" "$HOME/dev/backups/brain-db" "$HOME/dev/logs"
tar -czf "$HOME/dev/backups/brain-repo/$DATE.tar.gz" -C "$HOME/dev/repos" brain
rm -rf "$HOME/dev/backups/brain-db/$DATE"
gbrain export --dir "$HOME/dev/backups/brain-db/$DATE"
tar -czf "$HOME/dev/backups/brain-db/$DATE.tar.gz" -C "$HOME/dev/backups/brain-db" "$DATE"
rm -rf "$HOME/dev/backups/brain-db/$DATE"
find "$HOME/dev/backups/brain-repo" -name '*.tar.gz' -type f -mtime +30 -delete
find "$HOME/dev/backups/brain-db" -name '*.tar.gz' -type f -mtime +30 -delete
echo "$(date -Is) gbrain backup ok" >> "$HOME/dev/logs/gbrain-backup.log"
SCRIPT
chmod +x "$HOME/dev/scripts/gbrain-backup.sh"

(crontab -l 2>/dev/null; echo '17 3 * * * $HOME/dev/scripts/gbrain-backup.sh >> $HOME/dev/logs/gbrain-backup.log 2>&1') | crontab -
```

## Restore smoke test

This verifies the markdown source backup can restore into a scratch repo and that
Gbrain can import/search it. It does not overwrite the live brain.

```bash
set -euo pipefail
export PATH="$HOME/.bun/bin:$PATH"
DATE=$(date +%F)
SCRATCH="$HOME/dev/tmp/brain-restore-$DATE"
rm -rf "$SCRATCH"
mkdir -p "$SCRATCH"

tar -xzf "$HOME/dev/backups/brain-repo/$DATE.tar.gz" -C "$SCRATCH"
test -f "$SCRATCH/brain/RESOLVER.md"
test -f "$SCRATCH/brain/retrospectives/2026-05-phase-1-thru-11.md"

gbrain import "$SCRATCH/brain" --no-embed
gbrain search "Phase 11 review gates"
gbrain doctor --json
```

Expected result:

- Import succeeds
- Search returns the Phase 11 PR summary or retrospective
- `gbrain doctor --json` returns usable health with no fatal errors. Warnings about
  missing embeddings are acceptable until an embedding provider is configured.

## Full restore after live corruption

1. Stop any Gbrain cron jobs or daemons.
2. Move the corrupt live content aside:

```bash
mv "$HOME/dev/repos/brain" "$HOME/dev/repos/brain.corrupt.$(date +%s)"
```

3. Restore the latest repo archive:

```bash
mkdir -p "$HOME/dev/repos"
tar -xzf "$HOME/dev/backups/brain-repo/<DATE>.tar.gz" -C "$HOME/dev/repos"
```

4. Re-import into Gbrain:

```bash
export PATH="$HOME/.bun/bin:$PATH"
gbrain import "$HOME/dev/repos/brain" --no-embed
# If an embedding provider is configured later:
# gbrain embed --stale
```

5. Verify:

```bash
gbrain search "Phase 11 review gates"
gbrain doctor --json
```

## Current Phase 12 verification

Manual backup and restore smoke test were run on 2026-05-11. Keyword search worked.
Doctor reported warnings for missing embeddings/provider, which is expected in the
keyword-only setup.
