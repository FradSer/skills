Feature: Unified design-engineering skill with integrated Emil Kowalski and Jakub Krehel workflows

  Scenario: Derived Emil reference packs strip standalone greeting sections and rewrite cross-pack references
    Given upstream Emil Kowalski skills and Jakub Krehel skills are packed into design-engineering
    When tools/skill-sync/interfaces.py builds the reference tree
    Then no Emil overview.md retains a standalone "## Initial Response" greeting section
    And intra-pack prose references to "SKILL.md" are rewritten to "overview.md"
    And cross-pack references between Emil workflows point to "references/emil/<name>/overview.md"

  Scenario: Unified capability routing maps every design, motion, review, exploration, and stress task
    Given an agent loads skills/design-engineering/SKILL.md
    When it routes an implementation, review, motion, variant/prototype, stress-test, or platform request
    Then a single unified capability matrix and lifecycle map pair the primary workflow with the matching craft and domain references
    And every markdown reference under skills/design-engineering/references/ is reachable from SKILL.md

  Scenario: Overlapping workflows and numerical craft rules are explicitly reconciled
    Given overlapping rules exist between Jakub's domain references and Emil's craft references
    When SKILL.md defines the fused system
    Then it reconciles press scale, easing curves, stagger timing, reduced-motion handling, variant/prototype pickers, and break/break-ui harnesses
    And it defines how review-animations, improve-animations, and find-animation-opportunities compose with holistic and change reviews
