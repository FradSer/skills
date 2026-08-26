Feature: STORM long-form article generation as a portable skill

  Scenario: The storm skill is a single self-contained directory
    Given the skills repository distributes one skill per directory
    When the storm skill is packaged from the dotclaude plugin
    Then skills/storm/SKILL.md is the only user-facing entry point
    And the engine methodology lives under skills/storm/references/
    And the four phase workflows live under skills/storm/references/
    And skills/storm does not contain a nested plugin or agents directory

  Scenario: The skill does not depend on a specific agent runtime
    Given the original plugin referenced Task subagents and ToolSearch
    When the workflow text is reviewed for runtime coupling
    Then it names no proprietary tool such as "ToolSearch" or "AskUserQuestion"
    And parallelism is expressed as spawn-subagents-if-available with a sequential fallback
    And retrieval is expressed as probe-available-search-tooling with web search as fallback
    And a missing topic is resolved by asking the user through any available prompt mechanism

  Scenario: Each phase is independently runnable and resumable
    Given a run directory already holds completed artifacts
    When the skill is re-invoked without --force for a completed phase
    Then that phase is skipped and its artifact is loaded instead
    And run-config.json records the phase as skipped
    When the skill is re-invoked with --force
    Then every phase runs again regardless of existing artifacts

  Scenario: An article is never written without research grounding
    Given the research phase has not produced research/sources.json
    When an outline or write invocation starts
    Then it stops and directs the user to run the research phase first
    And it does not fall back to parametric-only output as a final artifact

  Scenario: Citations stay verifiable end to end
    Given sources collected during research carry sequential ids
    When sections are written with inline citations
    Then every [n] resolves to an id in research/sources.json
    And uncited sources never appear in the References section
    And cited snippets have their embedded [n] stripped before reuse
