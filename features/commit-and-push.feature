Feature: Commit and push stays inside its authorization

  Scenario: Push only after an explicit commit-and-push request
    Given the user asks only to commit
    When the commit is created
    Then no push runs and the commit skill owns the request

  Scenario: Refuse to publish a protected branch
    Given the current branch is main, master, develop, or production
    When a commit-and-push request arrives without naming that branch
    Then the push is refused and the refusal is reported

  Scenario: Refuse to publish a detached HEAD
    Given HEAD does not name a branch
    When a push would run
    Then the push is refused

  Scenario: Treat a rejected push as a reportable failure
    Given the remote rejects the push
    When the failure is handled
    Then no force-push, amend, or alternate remote is attempted
    And the failure is reported

  Scenario: Report the result facts
    Given a commit and push completed
    When the result is reported
    Then the commit hash, branch, remote, and push result are named