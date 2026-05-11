# Delete Gbrain Memory

Updated: 2026-05-11

## Purpose

Remove bad, private, or out-of-policy content from Gbrain. Removing the source
markdown file is not enough: Gbrain may have created chunks, links, facts, and
search indexes. Always delete from both the source repo and the Gbrain database.

## When to use

Use this runbook when:

- A source file accidentally contains sensitive content
- A page is out of policy under `policies/GBRAIN_POLICY.md`
- Search returns unexpected personal content
- A project should be removed from the brain
- A test/sentinel page must be cleaned up

## Deletion levels

### Level 1 — Page deletion

Use when one page/slug is bad.

1. Identify the slug:

```bash
export PATH="$HOME/.bun/bin:$PATH"
gbrain search "content pattern or entity name"
gbrain list -n 50
```

2. Remove the source markdown file from `~/dev/repos/brain` if it exists:

```bash
cd "$HOME/dev/repos/brain"
git rm path/to/file.md
git commit -m "chore: remove out-of-policy brain page"
```

3. Soft-delete the page from Gbrain:

```bash
gbrain delete <slug>
```

4. Verify it is hidden from normal search:

```bash
gbrain search "deleted content pattern"
```

Expected: `No results.`

5. Verify soft-delete state if needed:

```bash
gbrain call get_page '{"slug":"<slug>","include_deleted":true}'
```

Expected: `deleted_at` is non-null.

6. Hard-purge immediately if the content was sensitive:

```bash
gbrain call purge_deleted_pages '{"older_than_hours":0}'
```

7. Verify hard purge:

```bash
gbrain call get_page '{"slug":"<slug>","include_deleted":true}'
```

Expected: page not found.

### Level 2 — Source/project deletion

Use when an entire project/source is bad.

1. Remove the source files:

```bash
cd "$HOME/dev/repos/brain"
git rm -r projects/<project-slug>
git commit -m "chore: remove <project-slug> from brain corpus"
```

2. Search for remaining pages:

```bash
gbrain search "<project-slug>"
```

3. Delete each returned slug with Level 1 deletion.

4. If the source was registered separately, inspect sources:

```bash
gbrain sources list
```

Only use `gbrain sources remove <id> --confirm-destructive` after explicit human
approval, because it is a destructive source-level operation.

## Backup cleanup for sensitive content

If the deleted content was sensitive, delete backup snapshots that contain it
within the 30-day retention window:

```bash
# Inspect archives before deleting if unsure.
find "$HOME/dev/backups/brain-repo" -name '*.tar.gz' -type f -print
find "$HOME/dev/backups/brain-db" -name '*.tar.gz' -type f -print

# Delete affected dates after confirming scope.
rm "$HOME/dev/backups/brain-repo/<DATE>.tar.gz"
rm "$HOME/dev/backups/brain-db/<DATE>.tar.gz"
```

Do not delete all backups blindly. Preserve the most recent clean backup if one
exists.

## Sentinel deletion smoke test

A Phase 12 deletion test was performed with synthetic content only:

- Slug: `sentinel-test-target-phase-12`
- Sentinel string: `PHASE12_SENTINEL_DELETE_ME_7F3A`

Procedure used:

```bash
cat > /tmp/sentinel-test-target-phase-12.md <<'EOF'
# Sentinel Test Target Phase 12

This page contains the deletion sentinel entity: PHASE12_SENTINEL_DELETE_ME_7F3A.
It is safe synthetic content created only to test Gbrain deletion.
EOF

gbrain put sentinel-test-target-phase-12 < /tmp/sentinel-test-target-phase-12.md
gbrain search "PHASE12_SENTINEL_DELETE_ME_7F3A"
gbrain delete sentinel-test-target-phase-12
gbrain search "PHASE12_SENTINEL_DELETE_ME_7F3A"
gbrain call get_page '{"slug":"sentinel-test-target-phase-12","include_deleted":true}'
gbrain call purge_deleted_pages '{"older_than_hours":0}'
gbrain call get_page '{"slug":"sentinel-test-target-phase-12","include_deleted":true}'
```

Observed result:

- Sentinel was findable before deletion.
- Sentinel disappeared from normal search after soft-delete.
- `include_deleted` showed a non-null `deleted_at`.
- `purge_deleted_pages` hard-deleted the slug.
- Subsequent `get_page` returned page not found.

## Notes

- `gbrain delete` is a soft delete with a 72-hour recovery window.
- In Gbrain 0.32.0, hard purge is available through:

```bash
gbrain call purge_deleted_pages '{"older_than_hours":0}'
```

- The CLI help mentions page purge internals, but the reliable Phase 12 command is
  the raw tool call above.
