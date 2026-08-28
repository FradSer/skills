Feature: Gitflow branch lifecycle management as a unified skill

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
