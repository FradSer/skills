Feature: One discoverable marketing router over fifty bundled workflows

  Scenario: The mirror exposes only the marketing skill
    Given upstream coreyhaines31/marketingskills publishes fifty sibling skills
    When tools/skill-sync/marketing.py builds skills/marketing
    Then each upstream skill becomes <domain>/<domain>.md beside the router
    And no routed document keeps discovery frontmatter or its own SKILL.md
    And upstream evals and agents metadata are not copied
    And the upstream MIT license stays in the skill directory

  Scenario: Routing reaches one workflow before work starts
    Given an agent loads skills/marketing/SKILL.md
    When it receives a marketing request
    Then it reads product-marketing/product-marketing.md for product context first
    And it matches the request to one row of the generated index table
    And it reads the routed document before writing, drafting, auditing, or planning
    And it names any part of the request that no routed workflow covers

  Scenario: The generated index stays aligned with the mirrored tree
    Given routes.yml holds one generated row per routed workflow
    When tools/skill-sync/gen-index.py renders the sub-skill index
    Then every routed workflow appears in the table with its entry link
    And every markdown file under skills/marketing is reachable from SKILL.md
    And bash skills/marketing/scripts/sync-marketing.sh --check reports upstream drift