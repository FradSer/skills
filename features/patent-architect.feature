Feature: Patent drafting keeps legal conclusions and evidence boundaries

  Scenario: Never state a legal conclusion
    Given a prior-art comparison is complete
    When the draft is reported
    Then no conclusion of novel, patentable, grantable, or ready to file is stated

  Scenario: Keep the attorney boundary
    Given a disclosure draft exists
    When the result is described
    Then legal, filing, novelty, inventive-step, enablement, and claim-scope decisions stay with a patent attorney or office

  Scenario: Require a source ledger entry for every prior-art assertion
    Given a source supports a comparison
    When the assertion is written
    Then the ledger records the identifier, title, jurisdiction, dates, URL, retrieval date, and supporting passage

  Scenario: Treat a snippet as a lead
    Given only a search snippet is available
    When a comparison is drafted
    Then the snippet is checked against the source page or official record first

  Scenario: Report missing retrieval instead of inventing it
    Given no retrieval tool is available
    When prior art is requested
    Then the report says retrieval was unavailable and no search result is fabricated

  Scenario: Protect a confidential disclosure
    Given the user marks the disclosure confidential
    When retrieval is planned
    Then only a redacted or local corpus is used, or the safe search scope is confirmed first

  Scenario: Do not act without authorization
    Given a draft is complete
    When the user has not authorized it
    Then no filing, cloud document, or attorney contact occurs