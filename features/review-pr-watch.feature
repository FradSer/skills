Feature: Watch PR events without losing them to output filtering

  Scenario: review-pr arms one poll per cycle through the host wake facility
    Given review-pr has completed its baseline review for an open PR
    And the host returns a bounded command's output in a later turn
    When the workflow enters its persistent monitoring phase
    Then it arms one review-loop poll through that facility
    And it carries every poll event in the poll result
    And it re-arms the next poll after triaging each batch
    And it names no tool the host may not have
    And it does not use a manual foreground loop

  Scenario: review-pr reports a host without a continuation facility
    Given the host exposes no way to return a poll result to a later turn
    When the workflow enters its persistent monitoring phase
    Then it reports that ongoing monitoring could not be established
    And it stops after one bounded poll
    And it does not invent a monitor tool

  Scenario: review-pr asks before merging a settled PR
    Given CI is passing and every review comment has been triaged for an open PR
    When the workflow reaches closeout
    Then it presents the review summary and asks the user to confirm the merge
    And its closeout hook and every handoff reference preserve that confirmation gate
    And it merges only after the user explicitly confirms

  Scenario: A settled gate keeps the watch armed
    Given CI is terminal and passing and every comment received so far is triaged
    And the PR is still open and unmerged
    When the workflow prepares closeout
    Then it keeps the wake source armed
    And it reports only what changed on later polls
    And it does not treat the settled gate as a stop signal

  Scenario: Stop the watch only on a terminal outcome
    Given the workflow is watching an open PR
    When the PR merges, the user stops the watch, or the deadline expires
    Then it stops the wake source

  Scenario: A declined merge keeps waiting for review
    Given the user declines the merge while the PR stays open
    When the workflow continues the watch
    Then it keeps the wake source armed
    And it clears state only after the user also declines further watching

  Scenario: A watch that lost its wake source is reported
    Given a review watch is armed and has not polled for three intervals
    And the watch deadline has not passed
    When the turn-end guard checks the watch state
    Then it names the PR and the release path
    And it asks for the next poll rather than a silent comment queue

  Scenario: A fresh or finished watch never blocks a turn
    Given the watch polled within one interval, or its deadline passed, or a user decision is pending
    When the turn-end guard checks the watch state
    Then it passes without output
    And a subagent stop and a continuing turn also pass

  Scenario: Releasing a finished watch removes only its own state
    Given watch state exists for PR 7 and PR 8
    When the watch for PR 7 is released
    Then only the PR 7 state is removed

  Scenario: review-pr cleans a linked worktree and its PR branch after a confirmed merge
    Given a confirmed PR merge completed from a linked worktree on branch "feature/watch"
    When post-merge cleanup runs
    Then it removes the linked worktree from the main worktree
    And it fast-forwards the PR base branch explicitly from its origin ref before deleting branches
    And it explicitly deletes local branch "feature/watch" after synchronizing its base branch
    And unrelated branches and worktrees require separate explicit cleanup authorization
    And it does not report success until cleanup completes

  Scenario: Yield while an explicit merge decision is pending
    Given the closeout summary has been presented and merge confirmation is pending
    When the stop hook checks the awaiting-confirmation state
    Then it allows the turn to end and preserves the pending state
    And it does not merge before the user's reply

  Scenario: Resume closeout after confirmation
    Given the user confirms the presented merge while closeout is awaiting confirmation
    When the workflow resumes the approved merge
    Then it rearms the pending-operation reminder before verification and merge
    And it clears the state only after merge and authorized cleanup complete

  Scenario: Resolve material escalation before merge
    Given a review comment leaves correctness, authorization, or scope unresolved
    When review triage escalates it
    Then the agent continues independent work and requests the missing decision
    And it does not mark the merge gate ready until the decision is resolved

  Scenario: every PR handoff preserves the confirmed-merge contract
    Given create-pr, create-issues, and resolve-issues delegate PR review to review-pr
    When CI and comment triage finish
    Then every handoff reference and resolve-issues workflow instruction requires explicit user confirmation before merging

  Scenario: Creating a PR executes exactly one review-pr handoff
    Given create-pr has successfully created PR "https://github.com/octo/repo/pull/122"
    When the create-pr workflow reaches post-creation handoff
    Then it normalizes the PR number to "122"
    And it starts the standalone review-pr workflow with argument "122"
    And it does not finish after merely reporting the PR URL

  Scenario: An explicitly bounded PR request stops after its requested snapshot
    Given the user authorizes a draft PR and only one review and CI snapshot
    When create-pr finishes that snapshot
    Then it reports the PR URL and actual snapshot results
    And it does not start monitoring, comment, merge, or clean up branches
    And the explicit scope takes precedence over the full-workflow handoff

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

  Scenario: An expired watch exits before a metadata outage can restart polling
    Given the persisted watch deadline has passed
    And the PR metadata request is unavailable
    When the watch is restarted for PR "122"
    Then it emits a deadline event
    And it does not call the GitHub metadata or comment endpoints

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

  Scenario: A mismatched state file cannot expire a new PR watch
    Given a persisted deadline belongs to another PR or repository
    When the watch starts for PR "122"
    Then it ignores that deadline and reads metadata for PR "122"

  Scenario: An unacknowledged event replays when the API cursor advances
    Given the first poll emitted review node "PRR_kwPending" without acknowledgement
    And the next poll returns no comments newer than its cursor
    When the watch is restarted for PR "122"
    Then review node "PRR_kwPending" is emitted again

  Scenario: A successful poll cursor starts at the poll boundary
    Given a comment arrives while one poll is reading its endpoints
    When that poll succeeds
    Then its persisted cursor is no later than the poll start boundary

  Scenario: Exclusions also arrive through the EXCLUDE environment variable
    Given the EXCLUDE environment variable lists node "IC_kwHandled"
    When one poll returns that node together with a new review
    Then the excluded node is not emitted
    And the new review is emitted

  Scenario: Preserve tab characters across replay
    Given an unacknowledged comment contains a tab in its body
    When the watch persists and later replays it
    Then all comment context is retained

  Scenario: Continuous watch reacquires its lock per poll
    Given the watch runs continuously and the PR merges between two polls
    When the next poll starts
    Then the previous poll's lock has been released
    And the watch exits successfully with the merged status

  Scenario: An unfiltered watch still surfaces every new event
    Given no exclusions are configured
    When one poll returns an issue comment and a new review
    Then both events are emitted with their node and REST ids
