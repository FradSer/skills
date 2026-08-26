Feature: Watch PR events without losing them to output filtering

  Scenario: review-pr starts monitoring via the runtime monitor facility
    Given review-pr has completed its baseline review for an open PR
    When the workflow enters its persistent monitoring phase
    Then it starts a runtime-provided monitor for the review loop
    And it does not use a manual foreground loop or a runtime-specific monitor command

  Scenario: Creating a PR executes exactly one review-pr handoff
    Given create-pr has successfully created PR "https://github.com/octo/repo/pull/122"
    When the create-pr workflow reaches post-creation handoff
    Then it normalizes the PR number to "122"
    And it starts the standalone review-pr workflow with argument "122"
    And it does not finish after merely reporting the PR URL

  Scenario: create-pr uses a focused review-pr handoff reference
    Given review-pr is distributed as a standalone skill
    When create-pr reaches its post-creation phase
    Then it reads the focused review-pr handoff reference
    And it does not embed a second copy of the review-pr skill

  Scenario: create-pr keeps the review-pr fallback pack conventionally organized
    Given review-pr has important references and scripts
    When the create-pr reference pack is synchronized
    Then create-pr contains the review-pr workflow references directly under references
    And create-pr contains the review-pr monitoring and closeout scripts directly under scripts
    And create-pr does not contain a nested review-pr directory

  Scenario: A restarted watch resumes persisted PR state
    Given the watch persisted cursor "2026-08-15T08:00:00Z" and CI bucket "tests=pass"
    When the watch is restarted for PR "122"
    Then it starts comment polling from the persisted cursor
    And it restores the persisted CI bucket before emitting events

  Scenario: A crash before triage does not acknowledge a review comment
    Given the watch emitted review node "PRR_kwPending" without an acknowledgement
    When the watch is restarted for PR "122"
    Then review node "PRR_kwPending" is emitted again

  Scenario: An acknowledged review comment is suppressed on restart
    Given the watch acknowledged review node "PRR_kwHandled"
    When the watch is restarted for PR "122" with acknowledgement "PRR_kwHandled"
    Then review node "PRR_kwHandled" is not emitted

  Scenario: A new head commit resets persisted CI buckets
    Given the watch persisted head SHA "old-sha" and CI bucket "tests=pass"
    When the PR head changes to "new-sha"
    Then the persisted CI bucket is reset before polling

  Scenario: Metadata failure stops the watch without advancing the cursor
    Given the PR metadata request fails
    When the watch performs a poll
    Then it exits with a metadata error
    And it does not persist a current-time cursor

  Scenario: A watch stops at its persisted deadline
    Given the watch deadline has passed
    When the watch is restarted for PR "122"
    Then it emits a deadline event
    And it does not call the GitHub comment endpoints

  Scenario: A restarted watch suppresses already-triaged comments natively
    Given the watch excluded node "IC_kwHandled" via the --exclude flag
    When one poll returns that node together with a new review
    Then the excluded node is not emitted
    And the new review is emitted

  Scenario: Exclusions also arrive through the EXCLUDE environment variable
    Given the EXCLUDE environment variable lists node "IC_kwHandled"
    When one poll returns that node together with a new review
    Then the excluded node is not emitted
    And the new review is emitted

  Scenario: An unfiltered watch still surfaces every new event
    Given no exclusions are configured
    When one poll returns an issue comment and a new review
    Then both events are emitted with their node and REST ids
