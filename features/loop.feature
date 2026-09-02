Feature: Recurring agent work as a portable skill

  Scenario: The loop skill is cataloged as one portable skill directory
    Given the skills repository distributes one skill per directory
    When the loop skill is installed from the repository
    Then skills/loop/SKILL.md is its only user-facing entry point
    And the skill describes cloud and local scheduling capabilities without requiring a specific agent runtime

  Scenario: A fixed loop does not run twice at startup
    Given a user requests a fixed recurring prompt
    When the schedule is armed
    Then the prompt runs once immediately
    And the first scheduled wake occurs after one full interval

  Scenario: Changing a cloud schedule replaces the existing subscription
    Given a recurring cloud subscription already exists for the prompt
    When the user changes its interval or prompt
    Then the old subscription is removed before its replacement is created
