Feature: Explicit invocation of personal workflows in Codex

  Scenario: Workflow skills require an explicit invocation
    Given a personal workflow skill is installed from this repository
    When Codex discovers its agents/openai.yaml metadata
    Then implicit invocation is disabled
    And the skill remains available through an explicit skill mention

  Scenario: Commit, tool, and domain guidance can match a task automatically
    Given the commit, lark, or swiftui skill is installed
    When Codex discovers its agents/openai.yaml metadata
    Then implicit invocation is enabled

  Scenario: Invocation metadata travels with the skill
    Given the gitflow or storm skill includes references and scripts
    When its skill directory is installed or symlinked
    Then its agents directory is included alongside those resources
