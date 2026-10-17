# Marketing Skills Sync

**Upstream**: [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)
**Upstream branch**: `main`
**Upstream path**: `skills/`
**Last sync**: 2026-10-17
**Synced commit**: 365b412

## Provenance

Upstream publishes 50 sibling skills. This collection exposes exactly one skill,
`marketing`: each upstream skill becomes `<domain>/<domain>.md` beside the local
router, so no routed document is independently discoverable.

## Sync strategy

Run `bash skills/marketing/scripts/sync-marketing.sh` to update; use `--check`
for a read-only network drift check. The script clones upstream, builds a
complete candidate tree with
`uv run --no-project --with pyyaml python tools/skill-sync/marketing.py`, diffs
it against the installed tree, and renders the index table with
`tools/skill-sync/gen-index.py` from the generated `routes.yml`.

The local router `SKILL.md`, `README.md`, `SYNC.md`, `agents/` and `scripts/`
are preserved. Every other file is derived and rebuilt; do not edit derived
files directly. A malformed candidate aborts before replacing local files.

## Transforms

- Skill `SKILL.md` becomes `<domain>/<domain>.md`; discovery frontmatter is
  dropped, so the router index is the single routing index.
- Upstream `evals/` and `agents/` are not copied.
- Cross-skill links (`../../<other>/SKILL.md`) and intra-pack links
  (`../SKILL.md`) are rewritten to the mirrored paths.
- In-pack path mentions such as `` `references/scoring-criteria.md` `` become
  links, so every routed reference is reachable from the router.
- `routes.yml` keeps one row per workflow. The index `Use When` column is the
  first sentence of the upstream description, with the leading "When the user
  wants/needs to" clause dropped and the text capped at 220 characters.
- Upstream repository links are pinned to the synced revision.

## Known limits

- Upstream prose that names a sibling without a link (`cro`, `seo-audit`) keeps
  its prose form. Routing Rules step 5 in `SKILL.md` maps such a name to
  `<domain>/<domain>.md`.
- A bare `SKILL.md` mention inside a workflow names that workflow's own
  document; documents that describe the Agent Skills format keep the name.
- Links to the upstream `tools/` registry and integration guides stay on
  github.com at the synced revision. They need network access and are not
  mirrored, because upstream generates that registry.
- Six upstream example links used an unresolvable placeholder target. They now
  point at `https://example.com/<path>`.

## Backup retention

Backups preserve the complete previous skill tree in repository-level
`.backup/marketing/`, outside the installable skill. Each snapshot is unique;
existing snapshots are preserved and cleanup needs a separate request.

## License

Upstream is MIT (Corey Haines). `coreyhaines31-LICENSE.txt` stays in this
directory.