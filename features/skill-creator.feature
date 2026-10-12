Feature: Reliable internal skill tooling
  Scenario: Reject incomplete skill metadata
    Given a skill with an empty name, empty description, or no instructions
    When the validator checks it
    Then it reports an actionable validation failure

  Scenario: Package from an arbitrary working directory
    Given a valid skill with runtime resources and evaluation fixtures
    When the packaging script is invoked directly from another directory
    Then the archive contains runtime resources and excludes evaluation fixtures

  Scenario: Keep packaging inside the source boundary
    Given a skill containing a symlink to a file outside its directory
    When the skill is packaged
    Then no archive is published and the outside file is not copied

  Scenario: Avoid recursively packaging the output
    Given the output directory is also the skill directory
    When the skill is packaged
    Then the archive does not contain itself

  Scenario: Preserve valid YAML semantics
    Given quoted or multiline skill metadata
    When evaluation tooling reads the metadata
    Then it reads the same values as the YAML validator

  Scenario: Keep evaluation outages distinct from negative results
    Given an evaluation worker fails before measuring a trigger
    When results are aggregated for a request that should not trigger
    Then the case is reported as failed with the execution error

  Scenario: Keep training data when a class has one example
    Given one positive and one negative evaluation example
    When a holdout split is requested
    Then both classes retain training examples

  Scenario: Display untrusted evaluation text as data
    Given a prompt contains a closing script tag and HTML
    When a static review page is generated
    Then the prompt cannot escape the embedded JSON script

  Scenario: Keep viewer reads within the evaluation workspace
    Given output files or output directories link outside the workspace
    When the viewer discovers runs
    Then it excludes those links and does not embed outside content

  Scenario: Support mixed and nested run metadata
    Given numbered runs use a nested configuration layout and another run has no metadata
    When the viewer discovers runs
    Then it finds ancestor evaluation metadata and sorts unnumbered runs last

  Scenario: Preserve another service on the requested viewer port
    Given another local service occupies the requested port
    When the viewer starts
    Then it binds a free port without terminating another process

  Scenario: Reject meaningless or ambiguous evaluation inputs
    Given an empty evaluation set, duplicate query, or invalid execution count
    When an evaluation or improvement loop starts
    Then it rejects the input before launching a worker or reporting a score

  Scenario: Report only measured benchmark statistics
    Given one measured run and no baseline or token measurement
    When benchmark results are aggregated
    Then the reported run count is one and baseline deltas and tokens remain unmeasured

  Scenario: Ignore malformed run directory names
    Given a valid run and a malformed run directory
    When benchmark results are aggregated
    Then the valid run is retained and the malformed directory is reported and skipped
