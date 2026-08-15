Feature: Modern SwiftUI uses Liquid Glass as its primary macOS 26 and iOS 26 design system

  Scenario: A new Apple-platform feature targets macOS 26 and iOS 26 first
    Given an agent is asked to build or review SwiftUI UI
    When the request targets the current Apple platforms
    Then the skill prioritizes macOS 26 and iOS 26
    And it uses native Liquid Glass APIs before custom blur implementations

  Scenario: Liquid Glass remains a functional layer
    Given an agent is designing a SwiftUI feature
    When it decides where to apply Liquid Glass
    Then it reserves the material for controls, navigation, and transient functional UI
    And it does not turn ordinary content cards into glass by default

  Scenario: A review covers glass and general SwiftUI quality
    Given an agent reviews SwiftUI code that uses Liquid Glass
    When it reports confirmed findings
    Then it checks API availability, composition, interaction, accessibility, and performance
    And it uses the dedicated reference files for Liquid Glass and the authoritative Swift review standards

  Scenario: The unified SwiftUI skill is discoverable in both repository indexes
    Given a user browses the English or Simplified Chinese skill index
    When they look for modern SwiftUI guidance
    Then both indexes link to the swiftui skill
    And neither index presents a separate Liquid Glass-only skill

  Scenario: The unified skill is available to installed agent runtimes
    Given the SwiftUI skill is maintained in this repository
    When an agent runtime loads its shared skill directory
    Then the runtime resolves a swiftui symbolic link to the repository skill

  Scenario: Topics beyond Liquid Glass route to comprehensive references
    Given an agent works on state management, lists, layout, focus, charts, macOS scenes, localization, or previews
    When the SwiftUI skill is asked to implement or review that area
    Then it routes the task to a dedicated reference file vendored from AvdLee/SwiftUI-Agent-Skill
    And it still treats the local Liquid Glass and review references as the primary guidance

  Scenario: Authoritative review standards from twostraws are available
    Given an agent reviews Swift or SwiftUI code
    When the skill needs the full, specific review rules
    Then it reads the authoritative twostraws reference vendored in the skill

  Scenario: Hard correctness rules and API freshness guard every task
    Given an agent starts any SwiftUI task
    When it applies the skill
    Then it consults the latest-apis reference to avoid deprecated APIs
    And it checks the correctness checklist for hard rules that are always bugs

  Scenario: Liquid Glass reference covers verified background extension guidance
    Given an agent implements a detail column that should flow under a sidebar or inspector
    When it reads the Liquid Glass reference
    Then it finds backgroundExtensionEffect for stretching content
    And it does not find a fabricated scrollExtensionMode modifier
