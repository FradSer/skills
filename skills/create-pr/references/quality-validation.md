# Quality Validation Process

# Quality validation

Use the repository's declared scripts and CI as the source of truth. Prefer `pnpm`
when a pnpm lockfile is present and `uv run` for Python tools. Run the applicable
lint, typecheck, test, build, dependency, and security checks; do not invent a full
matrix of commands. The gate must pass before `gh pr create`, and failures must be
fixed or reported with the exact command/result.

Use a repository-defined security check or a targeted changed-file secret scan. Do not
print secret values or scan all history by default; a concrete finding may justify a
scoped follow-up.
