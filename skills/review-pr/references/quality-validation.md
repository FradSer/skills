# Quality Validation Process

# Quality validation for review fixes

Follow the repository's scripts and CI. Prefer `pnpm` with a pnpm lockfile and `uv run`
for Python tools, and rerun only checks affected by the fix plus required CI gates.
Use repository-defined dependency/security checks or a targeted changed-file scan. Do
not print secret values or scan all history by default; auth, missing-tool, flaky, and
infrastructure failures are surfaced for the user rather than auto-fixed.
