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
    And it uses the dedicated reference files for Liquid Glass and SwiftUI review guidance

  Scenario: The unified SwiftUI skill is discoverable in both repository indexes
    Given a user browses the English or Simplified Chinese skill index
    When they look for modern SwiftUI guidance
    Then both indexes link to the swiftui skill
    And neither index presents a separate Liquid Glass-only skill

  Scenario: The unified skill is available to installed agent runtimes
    Given the SwiftUI skill is maintained in this repository
    When an agent runtime loads its shared skill directory
    Then the runtime resolves a swiftui symbolic link to the repository skill
