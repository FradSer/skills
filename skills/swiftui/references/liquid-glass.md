# Liquid Glass for macOS 26 and iOS 26

Use this reference for custom Liquid Glass implementation, migration, and review. It complements native SwiftUI controls; it does not replace them.

## Design boundary

Liquid Glass is a dynamic material for a distinct **functional layer** above the **content layer**. Use it for controls, navigation, transient actions, and compact utility surfaces that act on content. Let underlying content remain visible and legible.

Do not apply glass merely because a surface is rounded or card-shaped. Avoid filling ordinary content lists, articles, forms, data cards, and every background with glass. Too much glass weakens hierarchy and can compromise readability.

Before custom work, build with the current SDK. Standard SwiftUI controls, toolbars, navigation, tab bars, menus, and sheets receive the system treatment automatically.

## Surface taxonomy: Glass vs. Materials vs. Cards

A fundamental design rule in modern SwiftUI is distinguishing between **Functional Chrome (Glass)** and **Content Surfaces (Materials)**.

| Layer / Surface | Recommended Material | Role & Reasoning |
| :--- | :--- | :--- |
| **Window & Sidebar** | System window background / `.sidebar` | Structural foundation; allows system materials to manage transparency. |
| **Content Cards** (Posts, Comments, PR details, Feed items) | `.regularMaterial` or grouped background + `.strokeBorder(.separator, lineWidth: 1)` | Neutral, stable canvas; preserves high text contrast and clear geometric bounds without optical distortion. |
| **Nested Reading Surfaces** (Code blocks, Diff hunks, Quotes) | `.regularMaterial` or `.thinMaterial` + `.strokeBorder(.separator, lineWidth: 1)` | Flat, non-refracting backdrop for monospace fonts and syntax highlighting. |
| **Floating Chrome & Controls** (Toolbars, FABs, HUDs) | `.glassEffect(.regular.interactive())`, `.buttonStyle(.glass)`, `.buttonStyle(.glassProminent)` | Floats above content; reacts optically to motion, touch/pointer, and surroundings. |
| **Status Chips & Small Badges** | `.background(.quaternary, in: Capsule())` | Compact, semantic labels; avoid heavy glass shaders on small static chips. |

### Why Content Cards Must NOT Use Liquid Glass (4 Traps)

1. **Legibility & Specular Distortion**: Liquid Glass introduces optical refraction, edge glow, and environment reflections. When applied to large reading surfaces (articles, markdown comments, code blocks), these optical properties destroy typography contrast, distort syntax colors, and cause visual fatigue.
2. **Layering & Nesting Collisions**: Content cards naturally contain nested elements (code blocks, blockquotes, diff snippets, status badges).
   - **Glass on Glass**: Stacking `.glassEffect` on `.glassEffect` doubles the tint and creates bizarre double refraction.
   - **Translucent Overlays on Glass**: Applying semi-transparent color fills (e.g. `.quaternary.opacity(0.25)`) over glass mixes with the glass refraction shader, producing muddy, dark, or unexpectedly discolored patches in dark mode.
3. **Semantic Misalignment**: Glass represents an interactive *lens* floating above content; it is not a *canvas* for reading. Placing long-form content inside glass violates HIG hierarchy.
4. **Scrolling & GPU Fill Rate**: Rendering dozens of independent `.glassEffect` shaders in a scrollable list forces excessive offscreen composition passes and degrades frame rates. Glass should be grouped in `GlassEffectContainer` for focused floating controls, not scattered across scrolling feed items.

### Content Card Pattern (Best Practice)

For content cards and nested reading containers, use standard Materials with a system separator border. Reserve Glass strictly for interactive action buttons inside the card:

```swift
struct ContentCard<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(16)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
            .overlay {
                RoundedRectangle(cornerRadius: 12)
                    .strokeBorder(.separator, lineWidth: 1)
            }
    }
}
```

Nested code block / suggested change container inside a card:

```swift
struct MarkdownCodeBlock: View {
    let code: String
    let language: String?
    var isSuggestion: Bool { language == "suggestion" }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 6) {
                Label(isSuggestion ? "Suggested change" : (language ?? "code"),
                      systemImage: isSuggestion ? "square.and.pencil" : "chevron.left.forwardslash.chevron.right")
                    .foregroundStyle(isSuggestion ? .green : .secondary)

                Spacer()

                // Interactive action uses Glass Button style
                Button("Copy code", systemImage: "doc.on.doc") {
                    NSPasteboard.general.clearContents()
                    NSPasteboard.general.setString(code, forType: .string)
                }
                .buttonStyle(.glass)
                .controlSize(.small)
            }
            .font(.caption.weight(.medium))
            .padding(.horizontal, 12)
            .padding(.vertical, 8)

            ScrollView(.horizontal) {
                Text(code)
                    .font(.system(.body, design: .monospaced))
                    .padding(.vertical, 2)
            }
            .scrollIndicators(.visible)
            .padding(.horizontal, 12)
            .padding(.bottom, 12)
        }
        // Unified Material card with system separator border — no glass on glass
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
        .overlay {
            RoundedRectangle(cornerRadius: 12)
                .strokeBorder(.separator, lineWidth: 1)
        }
    }
}
```

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
