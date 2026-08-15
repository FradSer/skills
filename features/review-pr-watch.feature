Feature: Watch PR events without losing them to output filtering

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
