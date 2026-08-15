Feature: Rank preferences without false substring matches

  Scenario: A short genre does not match a longer code prefix
    Given a listing has code "HSM-089"
    And the preferred genre is "SM"
    When recommendations are ranked
    Then the listing does not receive the "genre:SM" reason

Feature: Stop the MissAV workflow at the first access challenge

  Scenario: A challenge from a search page stops later searches and enrichment
    Given the MissAV browser reports a Cloudflare challenge on the first search
    When the recommendation workflow runs with another configured search query
    Then it exits with the blocked-access status
    And it does not visit the next search or any detail page

  Scenario: A challenge while enriching details is not reported as success
    Given listings were collected successfully
    And the MissAV browser reports a Cloudflare challenge on a detail page
    When the recommendation workflow enriches the ranked listings
    Then it exits with the blocked-access status
    And it does not report list-only recommendations as a successful run

  Scenario: A challenge body is detected even when the title is generic
    Given the MissAV browser title is not a challenge title
    And the page body says that JavaScript and cookies are required to continue
    When the browser checks the page for access control
    Then it records the challenge as a blocked access result
