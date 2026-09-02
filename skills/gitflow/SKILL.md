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
2. **Resolve Name/Version**: Infer or parse target branch name or semver version from `$ARGUMENTS`.
3. **Execute Start**: Run `scripts/start-branch.sh` with `--type <feature|hotfix|release>` and `--name <NAME_OR_TARGET>`.

### 2. Finishing a Branch (`finish`)

Follow the finish pipeline in [`references/gitflow-finish-pipeline.md`](references/gitflow-finish-pipeline.md):

1. **Pre-flight invariants**: Verify working tree is clean and current branch matches `<type>/*` per [`references/invariants.md`](references/invariants.md).
2. **Run Tests**: Verify project test suite passes before proceeding.
3. **Update Changelog**: Collect commits per [`references/changelog-generation.md`](references/changelog-generation.md), format following [`references/changelog-example.md`](references/changelog-example.md), and commit with attribution per [`references/coauthor-attribution.md`](references/coauthor-attribution.md).
4. **Execute Finish**: Run `scripts/finish-branch.sh` with `--type <feature|hotfix|release>` and `--name $NAME` or `--version $VERSION`.
5. **Post-finish Cleanup**: Prune stale branches and worktrees per [`references/cleanup.md`](references/cleanup.md).

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
