# Design Engineering Skills Sync

**Upstream**: [jakubkrehel/skills](https://github.com/jakubkrehel/skills) `skills/` (main branch)
**Upstream branch**: `main`
**Upstream path**: `skills/`
**Last sync**: 2026-10-14
**Synced commit**: d574cc8
**Design engineering upstream**: [emilkowalski/skills](https://github.com/emilkowalski/skills) `skills/` (main)
**Emil synced commit**: e8a175de22ae1e49370fc144c1f3bb9aeedf988d

## Provenance

This tree is the interfaces plugin content from the sibling `dotcodex`
repository, imported into this catalog on 2026-10-14. The upstream commits above
are the revisions that produced the imported content. Both imports use the same
generator and the same local router, so a later sync yields the same tree.

## Sync strategy

Run `bash skills/design-engineering/scripts/sync-interfaces.sh --force` to update;
use `--check` for a read-only network drift check. The script uses
`uv run --no-project --with pyyaml python` and
`tools/skill-sync/interfaces.py` to retain all upstream workflows while
exposing only `design-engineering`.

The local router `SKILL.md`, `README.md`, `SYNC.md`, `agents/` and
`scripts/` are preserved. Its upstream entry is retained as `upstream.md`,
with `review-format.md` beside it. Each of the ten other upstream skills becomes
`references/<domain>/overview.md`; the `better-` prefix is removed from domain
names. Supporting resources stay beside the overview. Only discovery frontmatter
and upstream agents metadata are removed. Complete workflow bodies, including
specialized output formats, remain intact. The router selects explanation,
variant, stress, change-review or domain modes from the user's request and
applies their reference contract instead of forcing a holistic report. Upstream
standalone command names are reference routing hints.

Emil workflows are retained under `references/emil/<name>/overview.md` with
their supporting resources, MIT license and the performance cheatsheet. Only
discovery frontmatter and agents metadata are removed; SKILL.md links become
overview.md links.

`tools/skill-sync/denest.py` rewrites cross-pack paths and names. Generated trees
are rebuilt so removed upstream references disappear. A malformed candidate
aborts before replacing local files. Do not edit derived files directly.

## Backup retention

Backups preserve the complete previous skill tree in repository-level
`.backup/interfaces/`, outside the installable skill. Each snapshot is unique;
existing snapshots are preserved and cleanup needs a separate request.

## License

Both upstreams are MIT. `jakub-LICENSE.txt` and
`references/emil/LICENSE.txt` stay in this directory.
