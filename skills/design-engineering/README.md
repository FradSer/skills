# Design Engineering Skill

Interface design, build, polish and review guidance. One router combines Jakub
Krehel's interface quality workflows with Emil Kowalski's design engineering
taste.

**Version**: 1.5.1
**Display Name**: Design Engineering

## What this skill does

The single discoverable router covers holistic and change-scoped reviews,
variant and state workbenches, stress tests, supplied-design implementation and
explanation. Thirteen upstream workflow packs stay available as references.

## Layout

- `SKILL.md` — the router. It selects the mode, applies the six quality domains
  and owns the review output format.
- `references/<domain>/overview.md` — derived upstream workflow packs. Each
  pack keeps its supporting resources beside its overview.
- `upstream.md` and `review-format.md` — the preserved holistic review
  contract.
- `agents/openai.yaml` — Codex invocation policy.
- `scripts/sync-interfaces.sh` — rebuilds the derived reference tree from both
  upstream repositories.
- `SYNC.md` — sync metadata and upstream revisions.

## Installation

```bash
npx skills add https://github.com/FradSer/skills --skill design-engineering
```

## Updating the reference tree

Router maintenance requires `git`, `uv` and network access to both upstream
repositories. The script runs the local generator with
`uv run --no-project --with pyyaml python`.

```bash
bash skills/design-engineering/scripts/sync-interfaces.sh --check
bash skills/design-engineering/scripts/sync-interfaces.sh --force
```

`SKILL.md`, this README, `SYNC.md`, `agents/` and `scripts/` are locally
owned and survive a sync. Every other file is derived; do not edit derived files
directly.

## License

MIT. Derived from [jakubkrehel/skills](https://github.com/jakubkrehel/skills) and
[emilkowalski/skills](https://github.com/emilkowalski/skills); both upstream
licenses stay in this directory.
