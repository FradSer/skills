# Quality validation

Before implementation, map the issue's explicit acceptance criteria to tests in the
existing suite. Include preserved boundary conditions, such as empty input, alongside
the reported failing behavior. In RED, verify that the bug test fails for the expected
reason; a preserved-boundary test may already pass. Keep both in the GREEN suite so
future regressions are detected. Ad hoc commands or manual assertions do not replace
these automated acceptance tests. Report any criterion that cannot be automated and
the concrete blocker rather than claiming complete regression coverage.

Inspect the repository's scripts, lockfiles, and CI before choosing checks. Use `pnpm`
for Node projects with a pnpm lockfile and `uv run` for Python tools. Run only the
applicable formatter, lint, typecheck, tests, build, and dependency/security checks;
the `create-pr` gate reruns the required set before opening the PR. Report missing
tools or failures explicitly.

Use repository-defined security checks, or a targeted changed-file scan when none is
defined. Never print secrets or scan all history by default; expand scope only when a
concrete finding or repository policy requires it.
