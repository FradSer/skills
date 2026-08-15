# Modern SwiftUI Review

Use this reference for implementation or review beyond the Liquid Glass API. Report only confirmed problems that matter to correctness, platform behavior, accessibility, performance, or maintainability.

## Modern API and view structure

- Prefer `foregroundStyle()` to `foregroundColor()` and `clipShape(.rect(cornerRadius:))` to `cornerRadius()`.
- Use `Tab`, `NavigationStack`, `NavigationSplitView`, typed `navigationDestination(for:)`, and current toolbar placements. Do not introduce deprecated navigation patterns.
- Prefer `containerRelativeFrame()`, `visualEffect()`, or a custom `Layout` before `GeometryReader`; do not use `UIScreen.main.bounds` for layout.
- Use `Label` when presenting a standard icon-and-text pair. Use semantic system styles and colors rather than manual opacity where they fit.
- Use `#Preview`, keep types focused, and extract genuinely independent or large subviews into their own `View` types rather than accumulating a monolithic `body`.
- Extract actions and business logic from `body`, `task`, and other view builders. Avoid `AnyView` unless type erasure is genuinely necessary.
- Use `.animation(_:value:)`, not the unscoped `animation(_:)` modifier. Keep motion purposeful and compatible with the Liquid Glass interaction.

## State, data flow, and concurrency

- Use `@Observable` for shared observable models. Mark them `@MainActor` unless the project uses main-actor default isolation.
- Keep owned `@State` private and local to the view that creates it. Use `@Bindable` or `@Environment` to pass observable models according to project conventions.
- Do not introduce `ObservableObject`, `@Published`, `@StateObject`, `@ObservedObject`, or `@EnvironmentObject` in new code unless bridging or a specific constraint requires it.
- Avoid `Binding(get:set:)` in `body` when normal state or an `onChange` effect can express the behavior.
- Prefer `async`/`await`, actors, and `Task`. Do not use GCD, `Task.detached()` without a well-established reason, or unsafe mutable shared state.
- Use `task()` for asynchronous work associated with a view’s lifetime. It automatically cancels when the view disappears.

## Navigation and presentation

- Register `navigationDestination(for:)` once per routed data type and do not mix it with legacy destination-based links in the same hierarchy.
- Attach `confirmationDialog()` to the control that triggers it so its presentation originates from the right source.
- Prefer `sheet(item:)` when presenting an optional item. Prefer native navigation and presentation components over manual overlays.
- Use standard navigation, toolbars, split views, and sheets before building a custom Liquid Glass navigation surface.

## Accessibility

- Support Dynamic Type with semantic fonts and flexible layout. Avoid fixed frames unless the content and hit target remain correct at larger text sizes.
- Use `Button` rather than `onTapGesture()` for actions unless tap count or location is needed. If a gesture is necessary, add the appropriate accessibility traits.
- Icon-only controls still need a text label for VoiceOver. Use `Button("Add", systemImage: "plus", action: add)` and `.labelStyle(.iconOnly)` where a visual icon-only treatment is required.
- Supply meaningful labels for nondecorative images and hide decorative images from accessibility.
- Respect Reduce Motion: replace large or disorienting motion with a less dynamic transition when needed.
- Do not make color the only signal. Honor `accessibilityDifferentiateWithoutColor` when color carries meaning.
- Design for touch, keyboard, pointer, and Voice Control. Interactive controls need a practical hit target, typically at least 44 by 44 points on iOS.

## Performance

- Treat `body` as frequently evaluated. Move expensive sorting, filtering, formatting, I/O, and nontrivial computation out of it.
- Prefer modifier values expressed with ternaries over branches that unnecessarily change structural identity.
- Avoid repeated inline collection transforms in `List` and `ForEach`. Derive transformed data from the source of truth and avoid stale caches.
- Use `LazyVStack` or `LazyHStack` for large scrollable collections.
- Keep view initializers inexpensive. Avoid work that can instead run in `task()`.
- Group related custom Liquid Glass effects in `GlassEffectContainer` rather than independently rendering a dense set of effects.

## Hygiene and validation

- Keep secrets out of source and user defaults. Use Keychain for credentials.
- Add focused tests for core logic. Add UI tests or inspect previews when visual behavior is the requirement.
- Run the project formatter, build, type checking, and relevant tests. Inspect the affected UI on each supported Apple platform.
- For Liquid Glass work, check light and dark appearance, Dynamic Type, VoiceOver, Reduce Motion, iPad/macOS resizing where applicable, and keyboard/pointer interaction on Mac.

## Provenance

This review baseline adapts the categories and guidance in [twostraws/swiftui-agent-skill](https://github.com/twostraws/swiftui-agent-skill): API, views, data, navigation, accessibility, performance, Swift concurrency, and hygiene. Confirm potentially changed API details in Apple documentation before proposing a migration.
