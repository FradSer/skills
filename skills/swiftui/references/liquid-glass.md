# Liquid Glass for macOS 26 and iOS 26

Use this reference for custom Liquid Glass implementation, migration, and review. It complements native SwiftUI controls; it does not replace them.

## Design boundary

Liquid Glass is a dynamic material for a distinct **functional layer** above the **content layer**. Use it for controls, navigation, transient actions, and compact utility surfaces that act on content. Let underlying content remain visible and legible.

Do not apply glass merely because a surface is rounded or card-shaped. Avoid filling ordinary content lists, articles, forms, data cards, and every background with glass. Too much glass weakens hierarchy and can compromise readability.

Before custom work, build with the current SDK. Standard SwiftUI controls, toolbars, navigation, tab bars, menus, and sheets receive the system treatment automatically.

## Core API patterns

### Custom, noninteractive glass surface

Apply the effect after modifiers that define the affected bounds and visual content.

```swift
Text("Pinned")
    .font(.headline)
    .padding(.horizontal)
    .padding(.vertical, 10)
    .glassEffect(.regular, in: .capsule)
```

### Interactive custom control

For custom interactive content that is not a standard button style, mark the material interactive and retain a semantic `Button` for the action.

```swift
Button("Show filters", systemImage: "line.3.horizontal.decrease.circle") {
    showFilters = true
}
.labelStyle(.iconOnly)
.frame(width: 44, height: 44)
.glassEffect(.regular.interactive(), in: .circle)
.accessibilityLabel("Show filters")
```

### Standard glass action

Use the native button style when it expresses the control.

```swift
Button("Save", systemImage: "checkmark", action: save)
    .buttonStyle(.glassProminent)
```

For a less prominent action:

```swift
Button("Share", systemImage: "square.and.arrow.up", action: share)
    .buttonStyle(.glass)
```

### Tint and clear variants

Use tint selectively to establish meaning or prominence. Use clear glass only where the backdrop reliably preserves contrast.

```swift
Text("Live")
    .padding(.horizontal)
    .padding(.vertical, 8)
    .glassEffect(.regular.tint(.orange), in: .capsule)
```

```swift
Label("Flag", systemImage: "flag.fill")
    .padding()
    .glassEffect(.clear, in: .rect(cornerRadius: 16))
    .background(.black.opacity(0.3), in: .rect(cornerRadius: 16))
```

Do not add `.interactive()` to static labels, backgrounds, or decorative effects.

## Grouped glass

Use one `GlassEffectContainer` for nearby custom effects that need to visually blend, coordinate during motion, or avoid independent rendering. It groups effect rendering and supports interaction between shapes.

```swift
GlassEffectContainer(spacing: 16) {
    HStack(spacing: 16) {
        Button("Previous", systemImage: "chevron.left", action: previous)
            .labelStyle(.iconOnly)
            .frame(width: 44, height: 44)
            .glassEffect(.regular.interactive(), in: .circle)

        Button("Next", systemImage: "chevron.right", action: next)
            .labelStyle(.iconOnly)
            .frame(width: 44, height: 44)
            .glassEffect(.regular.interactive(), in: .circle)
    }
}
```

The container `spacing` controls when nearby effect shapes begin to blend. A larger value starts blending at a greater distance. Match it to the layout spacing, then inspect the result in motion rather than guessing a universal constant.

Do not wrap unrelated effects scattered throughout a screen in one giant container. Do not create a container for one static effect without a reason.

## Purposeful morphs and unions

Use glass IDs and transitions only for an animated insertion, removal, expansion, or collapse where people should perceive one functional surface becoming another. Keep every related shape inside the same container and namespace.

```swift
@State private var isExpanded = false
@Namespace private var glassNamespace

var body: some View {
    GlassEffectContainer(spacing: 12) {
        HStack(spacing: 12) {
            Button("Compose", systemImage: "square.and.pencil") {
                withAnimation(.spring) {
                    isExpanded.toggle()
                }
            }
            .labelStyle(.iconOnly)
            .frame(width: 44, height: 44)
            .glassEffect(.regular.interactive(), in: .circle)
            .glassEffectID("compose", in: glassNamespace)

            if isExpanded {
                Button("Attach", systemImage: "paperclip", action: attach)
                    .labelStyle(.iconOnly)
                    .frame(width: 44, height: 44)
                    .glassEffect(.regular.interactive(), in: .circle)
                    .glassEffectID("attach", in: glassNamespace)
                    .glassEffectTransition(.matchedGeometry)
            }
        }
    }
}
```

Use `glassEffectUnion(id:namespace:)` only when multiple glass effects with the same Glass variant and shape should contribute to a single effect shape. It is not a general-purpose layout modifier.

```swift
GlassEffectContainer(spacing: 12) {
    HStack(spacing: 12) {
        ForEach(tools) { tool in
            Image(systemName: tool.symbol)
                .frame(width: 44, height: 44)
                .glassEffect(.regular, in: .circle)
                .glassEffectUnion(id: tool.isPrimary ? "primary" : "secondary", namespace: glassNamespace)
        }
    }
}
```

## Background extension and edge-to-edge scrolling

Use `backgroundExtensionEffect()` to stretch a detail view's background under the sidebar or inspector so the glass surface reads as one continuous canvas. Apply it with discretion to a single background view; it mirrors the view at the edges, blurs the copies, and clips to avoid overlap.

```swift
NavigationSplitView {
    sidebar
} detail: {
    ZStack {
        banner
            .backgroundExtensionEffect()
        content
    }
}
.inspector(isPresented: $showInspector) {
    inspectorContent
}
```

To let a horizontal scroll view extend under the sidebar or inspector, make it touch the leading and trailing edges — the system then scrolls it under the sidebar or inspector automatically. There is no `scrollExtensionMode`-style modifier for this; do not invent one.

## Availability and migration

For apps supporting pre-26 releases, isolate only the visual treatment in availability branches. Keep view identity, action handling, content, accessibility, and state shared.

```swift
private var filterControl: some View {
    Button("Show filters", systemImage: "line.3.horizontal.decrease.circle") {
        showFilters = true
    }
    .padding(.horizontal)
    .padding(.vertical, 10)
    .modifier(FilterControlTreatment())
}

private struct FilterControlTreatment: ViewModifier {
    func body(content: Content) -> some View {
        if #available(iOS 26, macOS 26, *) {
            content.glassEffect(.regular.interactive(), in: .capsule)
        } else {
            content.background(.ultraThinMaterial, in: .capsule)
        }
    }
}
```

Use the availability condition that exactly matches the project’s platforms. Do not add a fallback when the deployment target is already macOS 26/iOS 26 or later.

## Review checklist

- The surface belongs to the functional layer and has a specific purpose.
- Standard SwiftUI components were retained where they meet the need.
- The native `glassEffect`, glass button style, or system component is used instead of an imitation.
- Layout, padding, shape, and foreground modifiers establish the correct glass bounds before `glassEffect`.
- Interactive effects map to actual semantic controls; decorative effects are not interactive.
- A container groups only nearby effects that need shared rendering or a morph.
- Transitions, IDs, and unions correspond to a visible hierarchy change and use one namespace.
- `backgroundExtensionEffect()` is limited to a single background view and only where content should flow under the sidebar or inspector; horizontal scrolls under a sidebar rely on edge-to-edge layout, not a made-up modifier.
- Text and icons remain legible over changing backdrops in light and dark appearances.
- The UI remains usable with Dynamic Type, Reduce Motion, VoiceOver, keyboard focus, and pointer interaction.
- Pre-26 fallback behavior is equivalent when the app supports it.

## Primary sources

- [Applying Liquid Glass to custom views](https://developer.apple.com/documentation/swiftui/applying-liquid-glass-to-custom-views)
- [GlassEffectContainer](https://developer.apple.com/documentation/swiftui/glasseffectcontainer)
- [GlassEffectTransition](https://developer.apple.com/documentation/swiftui/view/glasseffecttransition(_:))
- [backgroundExtensionEffect()](https://developer.apple.com/documentation/swiftui/view/backgroundextensioneffect())
- [Landmarks: Building an app with Liquid Glass](https://developer.apple.com/documentation/swiftui/landmarks-building-an-app-with-liquid-glass)
- [Materials HIG](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Build a SwiftUI app with the new design, WWDC25](https://developer.apple.com/videos/play/wwdc2025/323/)
