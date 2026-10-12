---
name: gitflow
description: "Manages local Git-flow branch lifecycles: start or finish feature, hotfix, and release branches with automated changelog generation, version bumping, and cleanup. Use for repositories configured for local Git-flow finishing when the user explicitly mentions git-flow branch operations (e.g. 'gitflow start feature', 'gitflow finish release'). For standard GitHub PR-based reviews and merges, use create-pr."
disable-model-invocation: true
---

# Git-flow Branch Lifecycle

Manage feature, hotfix, and release branch lifecycles using Git-flow conventions.

## Operations Overview

| Operation | Action | Target Branch | Base Branch | Merge Target |
|-----------|--------|---------------|-------------|--------------|
| **Start Feature** | Create branch | `feature/<name>` | `develop` | `develop` |
| **Finish Feature** | Merge & clean up | `feature/<name>` | — | `develop` |
| **Start Hotfix** | Create branch & bump patch | `hotfix/<version>` | `main` | `main` + `develop` |
| **Finish Hotfix** | Merge, tag & clean up | `hotfix/<version>` | — | `main` + `develop` |
| **Start Release** | Create branch & bump version | `release/<version>` | `develop` | `main` + `develop` |
| **Finish Release** | Merge, tag & clean up | `release/<version>` | — | `main` + `develop` |

## Workflow Routing

### 1. Starting a Branch (`start`)

Follow the start pipeline in [`references/gitflow-start-pipeline.md`](references/gitflow-start-pipeline.md):

1. **Pre-flight invariants**: Verify working tree is clean (`git status --porcelain` is empty) per [`references/invariants.md`](references/invariants.md).
2. **Resolve Name/Version**: Use the explicit target or a name grounded in the task. Resolve an ambiguous release version before mutation; preserve configured prefixes and version conventions.
3. **Execute Start**: Run `scripts/start-branch.sh` with `--type <feature|hotfix|release>` and `--name <NAME_OR_TARGET>`.

### 2. Finishing a Branch (`finish`)

Follow the finish pipeline in [`references/gitflow-finish-pipeline.md`](references/gitflow-finish-pipeline.md):

1. **Pre-flight invariants**: Verify working tree is clean and the entire current branch matches the configured prefix and requested target per [`references/invariants.md`](references/invariants.md).
2. **Run Tests**: Verify project test suite passes before proceeding.
3. **Update Changelog when required**: Preserve existing entries, collect commits per [`references/changelog-generation.md`](references/changelog-generation.md), and format following [`references/changelog-example.md`](references/changelog-example.md). Use [`references/coauthor-attribution.md`](references/coauthor-attribution.md) only when attribution is configured or requested.
4. **Execute Finish**: Run `scripts/finish-branch.sh` with `--type <feature|hotfix|release>` and `--name $NAME` or `--version $VERSION`.
5. **Verify the result**: Verify this operation's branch/tag and publication result. Read [`references/cleanup.md`](references/cleanup.md) for authorized cleanup; preserve unrelated branches and worktrees.

Remote pushes, tags, merges, release publication, and branch deletion are external or
destructive mutations. Use the scripts only after the user authorizes that operation.
Pass `--no-push` when only local work is authorized. It performs real local mutations,
including a finish's merges, tags, and local branch deletion; it is not a dry run. Scripts
retain publication by default for existing callers, so omit that flag only with remote
authorization. Never force-push or delete another branch. Check installed CLI capabilities
before mutation; validated version updates use `uv` and Python 3.11+.

## Supporting References & Scripts

- Start Pipeline: [`references/gitflow-start-pipeline.md`](references/gitflow-start-pipeline.md)
- Finish Pipeline: [`references/gitflow-finish-pipeline.md`](references/gitflow-finish-pipeline.md)
- Pre-flight Invariants: [`references/invariants.md`](references/invariants.md)
- Changelog Generation: [`references/changelog-generation.md`](references/changelog-generation.md)
- Changelog Example: [`references/changelog-example.md`](references/changelog-example.md)
- Co-author Attribution: [`references/coauthor-attribution.md`](references/coauthor-attribution.md)
- Branch & Worktree Cleanup: [`references/cleanup.md`](references/cleanup.md)
- Start Branch Script: `scripts/start-branch.sh`
- Finish Branch Script: `scripts/finish-branch.sh`
- Version Manifest Helper: `scripts/bump-version.py` — validates all supported package versions before writing
- Configuration Helper: `scripts/gitflow-config.sh` — resolves native topic/base and legacy Git-flow configuration
