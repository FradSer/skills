Feature: README updates match the repository they document

  Scenario: Structure a new collection repository README
    Given a repository that ships several independent items in its own directories
    When a new README is written
    Then the collection profile is used and each existing item directory is listed

  Scenario: Structure a new single-artifact repository README
    Given a repository that ships one package, app, library, or service
    When a new README is written
    Then the single-artifact profile is used
    And no catalog section is invented

  Scenario: Update an existing README without a license, badges, or translation
    Given a repository whose root README is the only README
    And no LICENSE file, no badge target, and no README.zh-CN.md
    When the README is updated from the current source
    Then the existing section structure and project voice are preserved
    And no License section, badge, or translation link is added

  Scenario: Keep a read-only review read-only
    Given the user asks only whether a README agrees with the current source
    When the requested review is complete
    Then the reported diff is not written until the user asks for a write

  Scenario: Report an unverified item instead of guessing
    Given a documented command, version, or component that no current file confirms
    When the README is updated
    Then the item is reported as uncertain rather than rewritten from assumption

  Scenario: Keep the English and Chinese files parallel
    Given bilingual synchronization is requested for a README pair
    When both files are updated
    Then they carry the same section order, links, commands, and scope