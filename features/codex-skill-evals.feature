Feature: Execute source skills in independent Codex CLI sessions

  Scenario: Record an actual explicit skill invocation
    Given a fresh fixture with a project-local skill snapshot
    When a new ephemeral Codex process receives an explicit skill request
    Then the transcript records a successful read of that project's SKILL.md
    And the completed task is graded against observable files and operations
    And the thread id, source hashes, transcript, final output, and usage are retained

  Scenario: Distinguish runtime failures from task outcomes
    Given a process error, malformed event stream, timeout, or missing completed turn
    When grading its output
    Then the run is an execution error rather than a passing negative test
    And unavailable token data remains unavailable

  Scenario: Isolate external operations
    Given an evaluation involving GitHub, Lark, or a browser
    When the skill runs in its temporary repository
    Then service commands use the recorded fixture CLI
    And Git publication targets a local bare repository
    And unrelated files and source skills remain unchanged

  Scenario: Exclude ambient credentials and preserve read-only requests
    Given the host environment contains an unrelated API key and shell startup setting
    When an independent case starts
    Then only the documented runtime variables reach the child
    And command networking and reads outside approved runtime paths are denied
    And a read-only case cannot change the document under review

  Scenario: Reject fabricated service success
    Given a model writes an alleged successful operation into a fixture log
    When no actual CLI command and matching parent-owned event receipt exist
    Then the alleged operation fails evaluation
    And a PR also requires its exact head on the local bare remote

  Scenario: Reproduce a demonstrated skill failure
    Given a completed independent run that violates the user's task contract
    When the source skill is repaired
    Then the same prompt and fixture run again in a fresh Codex process
    And both runs remain available for comparison

  Scenario: Reassess evidence after correcting the evaluator
    Given a saved run with its raw events and original result
    When the current evaluator reassesses the selected task
    Then it saves a separate assessment with the grader revision
    And it preserves the original transcript and result
    And an incomplete process still cannot pass

  Scenario: Require regression coverage for unchanged acceptance boundaries
    Given an issue requires trimming spaces and preserving an empty string
    When a fix adds tests only for trimming and checks the empty string manually
    Then the task fails its automated acceptance coverage check
    And a test that detects a future empty-string regression is required

  Scenario: Reject browsing after challenge detection
    Given the fixture browser reports a challenge and the wrapper returns 42
    When a later browser command scrolls, clicks, waits, or reads the page
    Then the task fails even if only one page was opened
    And closing the browser session remains permitted
