# Marketing Skill

Marketing workflow router. Fifty routed workflows cover positioning, content and
copy, SEO and AI search, conversion, paid and lifecycle, pricing, launch,
analytics, and growth engineering.

**Version**: 1.0.0
**Display Name**: Marketing

## What this skill does

One discoverable skill routes marketing requests to the workflow that owns the
deliverable. `product-marketing` supplies the product, audience, and positioning
context; the other workflows specialize in a channel, a funnel stage, or a
measurement problem.

## Layout

- `SKILL.md` — the router. It holds the routing rules and the generated index table.
- `<domain>/<domain>.md` — one routed workflow per domain, with its own reference
  routing and output contract. Supporting resources stay under `<domain>/references/`.
- `routes.yml` — the generated route manifest that the index table renders from.
- `agents/openai.yaml` — Codex invocation policy.
- `scripts/sync-marketing.sh` — rebuilds the derived documents from upstream.
- `SYNC.md` — sync metadata, upstream revision, and transforms.
- `coreyhaines31-LICENSE.txt` — upstream MIT license.

## Installation

```bash
npx skills add https://github.com/FradSer/skills --skill marketing
```

## Updating the routed workflows

Router maintenance requires `git`, `diff`, `uv`, and network access to the
upstream repository. The script builds a complete candidate tree with
`uv run --no-project --with pyyaml python tools/skill-sync/marketing.py`, then
renders the index table with `tools/skill-sync/gen-index.py`.

```bash
bash skills/marketing/scripts/sync-marketing.sh --check
bash skills/marketing/scripts/sync-marketing.sh --force
```

## License

MIT. Derived from
[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills);
the upstream license stays in this directory.