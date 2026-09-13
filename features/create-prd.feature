Feature: Evidence-preserving PRD revision
  Scenario: Broad repair does not approve invented policy
    Given a source defines separate event and silent recommendation rules
    When the user asks to fix all issues
    Then proposals remain separate from confirmed requirements
    And no shared time window or arbitrary duration is silently introduced

  Scenario: Simplification uses business rules rather than implementation detail
    Given the user rejects a complex diagram and requests a table
    When the section is replaced
    Then a business rule table replaces the diagram
    And conditions, operators, time anchors and action meanings are preserved

  Scenario: Online revision preserves concurrent changes
    Given a shared strategy table has newer edits
    When the user requests restoring multiline boolean conditions
    Then the latest baseline and intended changes are recorded first
    And only authorized cells are changed and read back
    And unrelated values and formatting remain unchanged
