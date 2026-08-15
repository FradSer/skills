---
name: swiftui
description: Build, refactor, or review modern SwiftUI. Prioritize macOS 26 and iOS 26 Liquid Glass, while covering architecture, state, concurrency, navigation, accessibility, performance, and code quality. Use for any SwiftUI implementation, migration, or review.
license: MIT
metadata:
  sources:
    - https://github.com/Dimillian/Skills/tree/main/swiftui-liquid-glass
    - https://github.com/twostraws/swiftui-agent-skill
    - https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass
---

# SwiftUI

Build and review modern SwiftUI as one integrated discipline: platform design, view architecture, data flow, concurrency, navigation, accessibility, performance, and testing. **macOS 26 and iOS 26 are the primary targets**, so start from the system’s Liquid Glass design and native SwiftUI APIs. Do not recreate Liquid Glass with blur, opacity, gradients, or custom overlays.

Standard SwiftUI components, navigation, toolbars, tab bars, menus, sheets, and controls already adopt the current system appearance. Start by using those components as intended; add custom glass only when a custom functional control needs it.

Read the focused reference before acting:

| Request | Read |
| --- | --- |
| Add, migrate, diagnose, or review Liquid Glass | [references/liquid-glass.md](references/liquid-glass.md) |
| Implement or review SwiftUI architecture, state, views, navigation, accessibility, performance, concurrency, or tests | [references/review.md](references/review.md) |

When a task spans both, read both files. Apple documentation is the source of truth whenever an API signature, platform availability, or behavior may have changed.

## First decisions

1. Identify the platform, deployment target, and supported OS versions from the project configuration. Treat macOS 26 and iOS 26 as the default for new apps.
2. Preserve standard components before customizing. Build with the current SDK and inspect the app on macOS 26 and iOS 26 before adding custom effects.
3. Classify each candidate surface:
   - **functional layer:** controls, navigation, toolbars, transient actions, floating utility controls, and other UI that acts on content. Liquid Glass is appropriate here.
   - **content layer:** reading, browsing, editing, data presentation, and ordinary cards. Do not make content glass by default; use layout, standard materials, grouping, or color only when they improve hierarchy.
4. State the smallest viable plan. Use a custom glass treatment only when a standard component cannot express the required interaction or hierarchy.

## Implementing Liquid Glass

Follow [references/liquid-glass.md](references/liquid-glass.md). The baseline is:

- Prefer `.buttonStyle(.glass)` or `.buttonStyle(.glassProminent)` for custom actions over applying `glassEffect` directly to a `Button`.
- For a custom functional surface, establish its size, padding, foreground style, and shape first, then apply `.glassEffect(_:in:)` last among modifiers that determine the glass bounds.
- Use `.regular` by default. Use `.clear` only when the content behind it still provides reliable contrast. Tint sparsely to communicate hierarchy or prominence, not decoration.
- Make a custom effect `.interactive()` only when its surface is directly interactive. A decorative glass view should not advertise interaction.
- Put nearby custom glass effects that need to blend, move together, or be rendered as a group inside `GlassEffectContainer`. Tune its spacing from the visual relationship; a larger value causes effects to start blending from farther apart.
- Add `glassEffectID`, `glassEffectTransition`, or `glassEffectUnion` only for a purposeful, animated hierarchy change within one `GlassEffectContainer` and one namespace. Do not add morphing for a static layout.
- Keep related shapes, spacing, and visual weight consistent. Favor system spacing and semantic fonts over fixed dimensions.

Use `#available(iOS 26, macOS 26, *)` only when the project supports earlier releases. Keep the fallback semantically and behaviorally equivalent, use standard platform materials where appropriate, and avoid duplicating business logic across branches.

## General SwiftUI standards

This is a SwiftUI skill, not a narrow visual-effect skill. Apply these standards to every SwiftUI request, whether it includes custom Liquid Glass or not.

Follow [references/review.md](references/review.md) for modern APIs, view composition, state and concurrency, navigation, accessibility, performance, and code hygiene. In particular:

- Use modern SwiftUI and Swift 6.2+ concurrency. Do not introduce UIKit or AppKit, third-party UI frameworks, or custom infrastructure unless the project or request requires it.
- Prefer `@Observable` models with explicit main-actor isolation when the project does not define main-actor default isolation. Keep state ownership local and private; pass shared observable state using SwiftUI’s current observation tools.
- Use `NavigationStack` or `NavigationSplitView`, typed `navigationDestination(for:)`, semantic `Label`s, `Button`s for actions, Dynamic Type, and meaningful accessibility labels.
- Respect Reduce Motion and accessibility settings. Ensure interactive controls have an adequate hit target; do not communicate meaning through color alone.
- Keep expensive work, transforms, filtering, and sorting outside `body`; use `task()` for asynchronous work that should cancel with the view. Avoid `AnyView`, unnecessary conditional view branches, and eager stacks for large scrollable collections.
- Keep views, actions, and types focused and test core logic outside views. Use `#Preview` and project-supported tests.

## Review workflow

Report confirmed issues only. Do not manufacture a checklist of minor preferences.

1. Read the relevant references and inspect the deployment target, affected views, state model, and navigation hierarchy.
2. Check hierarchy first: Liquid Glass belongs in the functional layer, standard components remain system-provided, and custom glass has a clear reason.
3. Check Glass correctness: availability, shape and modifier order, interactivity, grouping in `GlassEffectContainer`, contrast, and motion behavior.
4. Check modern SwiftUI: APIs, data flow, navigation, accessibility, performance, Swift concurrency, and hygiene.
5. Verify with the project’s formatter, build, tests, previews, or UI tests. Test macOS and iOS when the feature is cross-platform, including light/dark appearance, larger Dynamic Type, keyboard/pointer use on Mac, and Reduce Motion.

For every finding, give the file and line, the broken rule, why it affects the app, and a minimal before/after fix. Group findings by file and end with the highest-impact fixes first. Skip files with no confirmed issue.

## Sources

- [Apple: Adopting Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass)
- [Apple: Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views)
- [Apple: Materials HIG](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Dimillian/Skills: swiftui-liquid-glass](https://github.com/Dimillian/Skills/tree/main/swiftui-liquid-glass)
- [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill)
