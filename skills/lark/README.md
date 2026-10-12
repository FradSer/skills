# Lark Plugin

Feishu/Lark CLI skills router, powered by [larksuite/cli](https://github.com/larksuite/cli).

**Version**: 2.0.0
**Display Name**: Lark

## What This Plugin Does

Provides the unified router for Lark/Feishu operations — docs, sheets, IM, calendar, approval, attendance, drive, wiki, contacts, minutes, mail, tasks, events, video conferences, whiteboards, apps (Miaoda), and more.

## Architecture

Upstream `lark-cli` embeds all domain skills and reference documents directly in the CLI binary (`lark-cli skills list`, `lark-cli skills read <skill>`, `lark-cli skills read <skill>/<path>`).

- **`SKILL.md` (lark router)** — Top-level router discovered by agent harnesses. It indexes all embedded domain skills and instructs agents to read them dynamically via `lark-cli skills read <sub-skill>`.
- **`scripts/sync-lark.sh`** — Syncs and regenerates the `SKILL.md` routing table and `SYNC.md` version metadata directly from `lark-cli skills list`.
- **`SYNC.md`** — Sync metadata and tracking.

## Installation & Setup

```bash
# 1. Install lark-cli separately, using the package manager and authorization
#    appropriate for your machine. This skill never installs or upgrades it.
#    Verify first:
lark-cli --version

# 2. Configure app credentials only when the user explicitly requests setup
lark-cli config init

# 3. Log in only after explicit authorization
lark-cli auth login --recommend
```

## Updating Router Index

Router maintenance requires `lark-cli` and `uv`. The script runs the local index
generator with `uv run --no-project --with pyyaml python`; PyYAML is resolved in an
isolated uv environment. Normal routing through `lark-cli skills read` does not
require this Python helper or uv.

```bash
bash skills/lark/scripts/sync-lark.sh --check     # dry-run check
bash skills/lark/scripts/sync-lark.sh             # refresh index from installed lark-cli
```

## License

MIT. Sourced from `larksuite/cli`.
