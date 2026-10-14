# Lark CLI Skills Sync

**Upstream**: [larksuite/cli](https://github.com/larksuite/cli)
**Last checked**: 2026-10-14
**lark-cli version**: 1.0.97
**Synced commit**: b6d0473

## Architecture

Upstream `lark-cli` embeds all domain skills and reference markdown files into the CLI binary at build time. Agents load skill content on demand via:

```bash
lark-cli skills list                    # list all embedded skills (JSON)
lark-cli skills read <name>             # read a skill's main SKILL.md
lark-cli skills read <name>/<path>      # read a reference file under the skill
```

Because skills are embedded in the installed binary:
1. No local duplicate subdirectories (`lark-doc/`, `lark-base/`, etc.) are stored in this repository.
2. The skill router (`SKILL.md`) provides a unified index routing each domain to `lark-cli skills read <name>`.
3. The installed binary is authoritative. This repository stores a generated
   snapshot of the router table; run `sync-lark.sh --check` before claiming it
   is aligned. The CLI does not expose the upstream commit, so the commit
   field above is historical metadata rather than a live proof of provenance.

## Updating the Router

To refresh the `SKILL.md` Sub-skill Index table when `lark-cli` updates:

Install or provide `uv` before maintenance. Both check and refresh use
`uv run --no-project --with pyyaml python` for the local index generator; the
script reads embedded CLI metadata and does not authenticate or change account setup.

```bash
# Check if router index is in sync with installed lark-cli
bash skills/lark/scripts/sync-lark.sh --check

# Regenerate SKILL.md index table and update SYNC.md metadata
bash skills/lark/scripts/sync-lark.sh
```

The sync script runs `tools/skill-sync/gen-index.py --from-cli` to query `lark-cli skills list`, rebuild the index table between the `## Sub-skill Index` and `## Routing Rules` markers, and update `SYNC.md` headers.
