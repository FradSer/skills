# Decision Logic

## Branch-Based Decision Tree

- **On main/develop**: Create issue directly.
- **On PR branch**: Ask "Must this be fixed before merge?"
  - **Yes**: Comment in PR with detailed context and reasoning, don't create issue.
  - **No**: Create new issue for later with clear justification for scope separation.

## Issue Types

1. **Epic issues**: Multi-PR initiatives (no auto-close keywords).
2. **PR-scoped issues**: Single PR resolution (use auto-close keywords — only fire on the default branch; see `auto-closing-keywords.md`).
3. **Review issues**: Non-blocking feedback from PR reviews.

## Issue Creation Process

1. **Analyze context** from current repository state and existing issues.
2. **Determine issue type** based on scope and complexity.
3. **Create proper labels** if they don't exist, after confirmation for that write:
   ```bash
   gh label create "priority:high" --description "High priority - this sprint" --color "d73a4a"
   gh label create "priority:medium" --description "Medium priority - next sprint" --color "fbca04"
   gh label create "priority:low" --description "Low priority - backlog" --color "0075ca"
   # If a label already exists, inspect the command's explicit already-exists result;
   # do not suppress authentication, validation, or network failures.
   ```
4. **Create issue** with proper structure and labels.
5. **Link related items** if applicable.
