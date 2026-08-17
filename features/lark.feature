Feature: Lark CLI skill router delegates domain skills to lark-cli skills read

  Scenario: Router skill directs agents to embedded lark-cli skills
    Given an agent needs to perform an operation on Lark or Feishu
    When the agent loads the lark skill router
    Then it identifies that sub-skills are managed via "lark-cli skills read <sub-skill>"
    And it instructs the agent to read "lark-shared" first for authentication and security rules

  Scenario: Sub-skill Index provides runnable read commands for all domains
    Given the installed lark-cli provides embedded domain skills
    When the agent checks the Sub-skill Index in SKILL.md
    Then each sub-skill row contains a runnable "lark-cli skills read <name>" command
    And "lark-shared" is hoisted to the top of the index table

  Scenario: Reference documents are read via lark-cli skills read sub-paths
    Given an agent is following instructions in a domain skill
    When the skill references a secondary guidance file
    Then the router instructs the agent to read relative files via "lark-cli skills read <sub-skill>/<path>"
    And cross-skill references are read via "lark-cli skills read <other-skill>/<path>"

  Scenario: Local directory contains no obsolete duplicate sub-skill folders
    Given the lark skill relies on the embedded lark-cli binary for sub-skill contents
    When inspecting the "skills/lark" directory
    Then it contains no duplicate subdirectories for embedded skills

  Scenario: Sync tooling refreshes the router index from lark-cli skills list
    Given an updated version of lark-cli is available
    When the sync script runs
    Then it updates SKILL.md index table and SYNC.md version metadata from lark-cli
