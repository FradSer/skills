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

  Scenario: A challenge detected during listing extraction stops later searches
    Given the MissAV browser loads a search page
    And a Cloudflare challenge appears during listing extraction
    When the recommendation workflow runs
    Then it exits with the blocked-access status
    And it does not execute subsequent search queries

Feature: Recognize valid video detail pages across URL formats

  Scenario: Category prefixed detail URLs are recognized as valid video pages
    Given a detail URL is "https://missav.ws/dm1/cn/ssis-825"
    When the browser environment checks if the URL is bad for detail
    Then the URL is accepted as a valid detail page

  Scenario: Detail extraction supports category prefixed URLs
    Given a detail page URL is "https://missav.ws/dm247/cn/ssis-825"
    When detail page evaluation extracts video metadata
    Then the detail result is not marked as blocked

Feature: Accurately match user preferences and feedback signals

  Scenario: A keyword in the listing slug matches user keyword preferences
    Given a listing has slug "ssis-825-english-subtitle"
    And the preferred keyword is "english-subtitle"
    When recommendations are ranked
    Then the listing receives the "keyword:english-subtitle" reason

  Scenario: Signal extraction preserves explicit performers and extracts code
    Given an item has title "MIDV-123 三上悠亚" and performers "三上悠亚"
    When signals are extracted from the item
    Then the extracted code is "MIDV-123"
    And the extracted performers include "三上悠亚"

  Scenario: Dislike feedback removes matching code from liked codes
    Given preferences have liked code "SSIS-825"
    When dislike feedback is applied for code "SSIS-825"
    Then "SSIS-825" is removed from liked codes
    And "SSIS-825" is added to disliked codes

  Scenario: Description analysis executes when CLI overrides specify genres
    Given a listing has description "调教并受虐"
    When recommendations are ranked with CLI genres "SM" without a prefs file
    Then the listing receives description score bonus and reasons

Feature: End-to-end recommendation pipeline execution

  Scenario: Recommendation workflow executes search, ranking, enrichment, and re-ranking
    Given search results return valid listings
    And detail page returns plot description
    When the recommendation workflow runs end to end
    Then it outputs enriched recommendations ranked by preferences
    And it cleans up all temporary files

  Scenario: Detail enrichment fallback on non-challenge failure
    Given listings were collected successfully
    And detail pages fail due to ad redirects or missing description without challenge
    When the recommendation workflow enriches listings
    Then it falls back to list-only ranked results with success status

  Scenario: Workflow passes default search filter from preferences
    Given preferences configure default filter "chinese-subtitle"
    When the recommendation workflow builds search queries
    Then search URLs include the "filters=chinese-subtitle" parameter

  Scenario: Eval output parser recovers valid JSON from noisy browser stdout
    Given browser evaluation produces JSON preceded by log lines
    When the eval output is normalized
    Then valid JSON listings are successfully extracted

  Scenario: Building search URL validates non-empty query
    Given a search query consisting only of whitespace
    When the search URL is constructed
    Then it raises an error requiring a non-empty search query

  Scenario: Preferences CLI provides usage help
    Given the user requests help from the preferences CLI
    When the help command is executed
    Then it exits with a successful zero status

Feature: Connect directly to existing user Chrome via CDP

  Scenario: Browser environment defaults to user Chrome mode
    Given no explicit browser mode is configured
    When the browser environment executes commands
    Then it defaults to user Chrome mode with CDP port 9222

  Scenario: Explicit isolated mode disables user Chrome
    Given isolated browser mode is explicitly requested
    When the browser environment executes commands
    Then it spawns an isolated browser session instead of attaching via CDP

  Scenario: User Chrome connection uses CDP port without isolated sandbox
    Given user Chrome is running with remote debugging port 9222
    When the browser environment executes commands
    Then it attaches via CDP port 9222 instead of spawning an isolated browser

  Scenario: User Chrome mode preserves running browser on start and close
    Given user Chrome mode is enabled
    When the workflow starts and closes browser sessions
    Then it does not kill or close the user's running Chrome instance



