# Git-flow start pipeline

Read [invariants.md](invariants.md) before starting a branch.

## Resolve the target

Use the user's explicit name or version. For a feature request with a clear task but
no slug, derive a short kebab-case name and state it before creating the local branch.
For a release or hotfix, preserve the project's release/version convention. Propose a
version from reachable tags and commits only when the request authorizes choosing it;
ask when the version or release scope is unresolved. Do not infer a release version
from an unrelated highest tag or assume an unversioned project starts at 0.0.0.

For git-flow-next, read `gitflow.branch.<type>.prefix`, `.parent`, and `.startpoint`,
and verify referenced nodes have `.type=base`. Feature parent is its development base;
release startpoint is its development base; a classic hotfix uses the feature parent
as the return/integration branch. The shared helper also reads legacy AVH
`gitflow.prefix.<type>` and `gitflow.branch.master/develop` when native topic keys are
absent. Native keys take precedence. Examples use conventional prefixes; actual names
and base branches come from repository configuration.

## Validate before mutation

Require a clean working tree, an existing configured base, a valid new branch ref, and
a supported installed Git-flow CLI. The wrapper checks `git flow <type> start --help`
for the flags that disable fetch and automatic worktree creation.

An explicit `--version` requires at least one supported version manifest. The helper
validates every recognized manifest before branch creation and before writing any file.
It updates the root `package.json.version`, static `[project]` or `[tool.poetry]` versions,
`Cargo.toml [package].version`, or a single SemVer line in `VERSION`/`version.txt`.
Dynamic/inherited versions need the project's release tooling. Dependency and nested
metadata versions remain unchanged. Version updates require `uv` and Python 3.11+.

## Execute

For authorized local work:

```bash
bash <skill-dir>/scripts/start-branch.sh --type feature --name <name> --no-push
bash <skill-dir>/scripts/start-branch.sh --type release --version <version> --no-push
bash <skill-dir>/scripts/start-branch.sh --type hotfix --version <version> --no-push
```

Use `--name` without `--version` for a branch-only operation. The wrapper stages only
validated version paths and commits a real version change. `--no-push` performs actual
local mutations; it is not a dry run.

Existing script callers retain publication by default. Omit `--no-push` only when
publication to the configured origin is authorized. A missing origin fails before
branch creation. A push failure leaves the local branch in place, returns failure,
and must be reported; do not claim remote completion.

Use the wrapper when available. For a manual fallback, inspect current CLI help,
validate all proposed version edits before starting, disable automatic remote
operations, stage only the intended paths, and publish only the exact branch when
authorized. Do not improvise unsupported flags or initialize Git-flow configuration.
