# Quality validation

Choose commands from the repository's declared scripts and CI configuration; do not
run every command below by default. For Node projects prefer the package manager lock
file (`pnpm` when `pnpm-lock.yaml` exists), then run only applicable lint, typecheck,
test, build, and audit scripts. For Python projects prefer `uv run` with the project's
declared tools, then run the applicable formatter, linter, tests, type checker, and
audit. Record commands and results.

Run security checks that the repository already defines, or a targeted changed-file
secret scan when no project check exists. Do not print secret values or rescan full
history by default. A missing tool or authentication failure is a reported validation
blocker, not a reason to suppress the error.
