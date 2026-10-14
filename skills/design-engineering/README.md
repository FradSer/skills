# Design Engineering Skill

Interface design, build, polish and review guidance. A unified router and design engineering system combining Jakub Krehel's interface quality domains with Emil Kowalski's motion, craft, and interaction philosophy.

**Version**: 1.6.0
**Display Name**: Design Engineering

## What this skill does

The single discoverable router fuses the interface quality floor (accessibility, layout, writing, typography, colors, surfaces) with the design engineering craft ceiling (purposeful motion, fluid physics, micro-interaction restraint, and adversarial stress-testing). Twenty-five reference packs stay available as specialized workflows.

## Layout

- `SKILL.md` — the unified router and orchestrator. It reconciles craft parameters, selects modes, enforces non-negotiable escalation triggers, and owns review formats.
- `references/<domain>/overview.md` — Jakub Krehel's 6 domain quality packs (accessibility, layout, writing, typography, colors, ui) and 5 specialized mode packs (variant, state-machine, break, explain-interface, build-design).
- `references/emil/<name>/overview.md` — Emil Kowalski's 14 design engineering packs (animate, animate-expo, review-animations, improve-animations, find-animation-opportunities, animation-vocabulary, prototype, break-ui, mobile-native, apple-design, pick-ui-library, ask-sonner, write-swift, and emil-design-eng) plus the performance cheatsheet.
- `references/interface-review/overview.md`, `upstream.md`, and `review-format.md` — the preserved change-review and holistic review contracts.
- `agents/openai.yaml` — Codex invocation policy.
- `scripts/sync-interfaces.sh` — rebuilds the derived reference tree from both upstream repositories.
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
