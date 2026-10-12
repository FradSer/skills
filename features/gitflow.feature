Feature: Gitflow branch lifecycle management as a unified skill

  Scenario: Locate helper files with CDPATH configured
    Given Gitflow scripts are invoked through a relative project-local skill path
    And the caller has configured CDPATH
    When starting and finishing a local feature
    Then helper paths resolve without directory-search output or lookup redirection

  Scenario: Gitflow is a single standalone skill routing all branch lifecycle operations
    Given an agent is configuring git-flow branch operations
    When inspecting the skills directory
    Then skills/gitflow/SKILL.md is the only entry point for git-flow operations
    And skills/gitflow does not contain nested sub-skill directories
    And skills/gitflow/SKILL.md has model invocation disabled

  Scenario: Starting a branch routes to the start pipeline
    Given an agent needs to start a feature, hotfix, or release branch
    When the gitflow skill executes the start pipeline
    Then it enforces pre-flight working tree invariants
    And it creates the branch using start-branch.sh with appropriate type and name

  Scenario: Finishing a branch routes to the finish pipeline
    Given an agent needs to finish a feature, hotfix, or release branch
    When the gitflow skill executes the finish pipeline
    Then it verifies tests pass and updates the changelog
    And it merges and cleans up using finish-branch.sh

  Scenario: Finish only the exact current branch
    Given the current branch and the requested branch have the same type but different names
    When finishing the requested branch
    Then the operation fails before merging or deleting either branch

  Scenario: Fail before local finish when origin is missing
    Given remote publication is requested and origin is not configured
    When finishing a branch
    Then the operation fails before merging or deleting the branch

  Scenario: Surface a failed publication
    Given a local finish succeeds but the requested push fails
    When the finish script exits
    Then it returns failure and does not report the branch as finished successfully

  Scenario: Keep local operations local despite Gitflow defaults
    Given Gitflow has automatic remote operations configured
    When the wrapper is invoked with no push
    Then fetching, pushing, tag publication, and remote branch deletion are disabled

  Scenario: Validate all version updates before creating the branch
    Given a requested version is invalid, no manifest exists, or one manifest is unsupported
    When starting a versioned branch
    Then it fails without creating the branch or modifying any manifest

  Scenario: Preserve unrelated version declarations
    Given manifests contain package versions and dependency or metadata versions
    When bumping the package version
    Then only the package version fields change and formatting is retained where possible

  Scenario: Honor configured Gitflow prefixes
    Given the feature prefix is configured as work
    When starting and finishing a named feature
    Then the exact configured branch is used throughout

  Scenario: Use the installed git-flow-next classic preset
    Given a local fixture initialized by the installed CLI classic preset
    When a feature, release, or hotfix starts and finishes without publication
    Then the native configuration keys are honored and the branch and tag lifecycle completes

  Scenario: Preserve package manifest formatting
    Given a valid JSON manifest with custom spacing and nested version metadata
    When the root package version changes
    Then only the root version value changes in the original text

  Scenario: Preserve a linked worktree after finishing its branch
    Given a feature, release, or hotfix is checked out in a linked worktree
    And its development branch is checked out in the main worktree
    When the branch finishes locally with the installed git-flow-next CLI
    Then the completed merge and branch deletion return success
    And the linked worktree remains detached without forcing another checkout
    And both worktrees are preserved
