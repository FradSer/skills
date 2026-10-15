---
name: design-engineering
description: "Design, build, polish or review product interfaces with coherent visual taste, purposeful motion, usability and accessibility. Use for UI implementation, holistic or change reviews, prototypes, animation and mobile interaction work; route specialized tasks through references."
---

# Design and review the interface as one system

Build or review the whole experience: establish the product’s personality and interaction needs, make deliberate visual and motion choices, then test those choices against usability and accessibility.

This skill fuses two foundational perspectives into one unified design engineering practice:
1. **The Interface Quality Floor**: Non-negotiable usability, accessibility, hierarchy, and robustness from Jakub Krehel's domain methodologies ([Accessibility](references/accessibility/overview.md), [Layout](references/layout/overview.md), [Writing](references/writing/overview.md), [Typography](references/typography/overview.md), [Colors](references/colors/overview.md), and [UI Surfaces](references/ui/overview.md)).
2. **The Craft & Taste Ceiling**: Fluid physical dynamics, micro-interaction restraint, tactile feel, and high-craft execution from Emil Kowalski's [Design Engineering](references/emil/emil-design-eng/overview.md) philosophy.

Good design is not an afterthought; unseen details compound into interfaces that feel right. Design taste and interface correctness inform the same decisions, not separate audits.

## Unified Capability Routing

Choose the requested mode before acting. Specialized modes apply only when the user requests their specific workflow; never turn an explanation, variant build, or stress test into an unrequested review.

| Mode / Request | Primary Workflow | Craft & Domain References | Output Contract |
| --- | --- | --- | --- |
| **Holistic screen/flow review** | Router review engine | 6 quality domains + [Review Animations](references/emil/review-animations/overview.md) | Consolidated quick/full review format |
| **Change / PR / branch review** | [Change review](references/interface-review/overview.md) | [upstream.md](upstream.md), [review-format.md](review-format.md), 6 domains | Resolved blast radius + change findings |
| **Single domain review** | Matching domain pack | [Accessibility](references/accessibility/overview.md), [Layout](references/layout/overview.md), [Writing](references/writing/overview.md), [Typography](references/typography/overview.md), [Colors](references/colors/overview.md), or [UI](references/ui/overview.md) | That domain's reporting format |
| **Motion-specific review** | [Review Animations](references/emil/review-animations/overview.md) | [UI animations](references/ui/animations.md), [Performance cheatsheet](references/emil/performance-cheatsheet.md) | 10 motion standards table + motion verdict |
| **Motion audit & planning** | [Improve Animations](references/emil/improve-animations/overview.md) | [UI performance](references/ui/performance.md), [Audit catalog](references/emil/improve-animations/AUDIT.md) | Prioritized findings + self-contained plans under `plans/` |
| **Motion opportunity sweep** | [Opportunities](references/emil/find-animation-opportunities/overview.md) | [Animation vocabulary](references/emil/animation-vocabulary/overview.md) | 4-gate filtered proposals (restraint-first) |
| **Web motion implementation** | [Animate](references/emil/animate/overview.md) | [UI animations](references/ui/animations.md), [Enter/exit](references/ui/enter-exit.md), [Icon transitions](references/ui/icon-transitions.md) | Working motion code passing craft bar |
| **React Native / Expo motion** | [Animate Expo](references/emil/animate-expo/overview.md) | Reanimated 4, Gesture Handler, Haptics | UI-thread native motion implementation |
| **Apple-style fluid interface** | [Apple Design](references/emil/apple-design/overview.md) | Fluid physics, momentum, springs, rubber-banding | Fluid web implementation with velocity handoff |
| **Mobile web / PWA feeling** | [Mobile Native](references/emil/mobile-native/overview.md) | Viewport, touch-action, safe areas, 16px inputs | Targeted platform CSS/meta fixes |
| **Alternative exploration** | [Variants](references/variant/overview.md) & [Prototype](references/emil/prototype/overview.md) | Divergence axes, isolated harness, unified picker | 3–5 working variants; user chooses |
| **Stress testing real data** | [Break](references/break/overview.md) & [Break UI](references/emil/break-ui/overview.md) | Adversarial [Catalog](references/emil/break-ui/CATALOG.md), scenarios | Rendered scenario harness & observed breaks |
| **Component state workbench** | [State machine](references/state-machine/overview.md) | Isolated fixture workbench, switcher | Single component flipped through real states |
| **Implement design frames** | [Build design](references/build-design/overview.md) | Figma MCP, tokens, components | Scoped implementation, measured comparison |
| **Explain construction / effect** | [Explanation](references/explain-interface/overview.md) | Layer stack, paint order, techniques | Evidence-based recipe in words; no verdict |
| **Select UI dependencies** | [Library Selection](references/emil/pick-ui-library/overview.md) | Curated modern libraries (Base UI, Sonner, cmdk) | Opinionated dependency recommendation |
| **Toast notifications** | [Sonner](references/emil/ask-sonner/overview.md) | Headless / styling escalation ladder | Clean toast integration & troubleshooting |
| **Modern Swift implementation** | [Swift](references/emil/write-swift/overview.md) | Swift 6.3/6.4, value types, concurrency | Idiomatic Swift architecture & views |
| **Animation performance & frame budgets** | [Animation Performance](references/emil/animation-performance/overview.md) | [Performance cheatsheet](references/emil/performance-cheatsheet.md), [UI performance](references/ui/performance.md) | Diagnostic cause + GPU/composite fix |
| **Technical drawing & linework** | [Technical drawing](references/technical-drawing/overview.md) | Geometry, orthographic views, viewer | Exact vector drawings & viewer bundle |

## Composite Execution Chains

Do not treat reference packs as isolated silos. Real design engineering tasks compose references into coherent multi-step pipelines:

1. **Component Construction**:
   [Library Selection](references/emil/pick-ui-library/overview.md) (pick accessible primitive) → [Layout](references/layout/overview.md) & [Typography](references/typography/overview.md) (token mapping) → [Animate](references/emil/animate/overview.md) / [Apple Design](references/emil/apple-design/overview.md) (press feedback & fluid curves) → [Accessibility](references/accessibility/overview.md) & [Mobile Native](references/emil/mobile-native/overview.md) (WCAG & touch platform hygiene) → [Break UI](references/emil/break-ui/overview.md) (stress-test with realistic worst-case data); integrate [Technical drawing](references/technical-drawing/overview.md) when precision vector linework or geometric blueprints are required.

2. **Motion Polish & Craft**:
   [Opportunities](references/emil/find-animation-opportunities/overview.md) (filter candidates through frequency/purpose gate) → [Animate](references/emil/animate/overview.md) / [Animate Expo](references/emil/animate-expo/overview.md) (implement with `--ease-out`, no `scale(0)`, GPU-only) → [Animation Performance](references/emil/animation-performance/overview.md) & [Performance cheatsheet](references/emil/performance-cheatsheet.md) (diagnose dropped frames, enforce layout/paint/composite pipeline, eliminate recalc storms) → [Review Animations](references/emil/review-animations/overview.md) (verify against 10 craft standards).

3. **Design Exploration**:
   [Variants](references/variant/overview.md) & [Prototype](references/emil/prototype/overview.md) (choose 1 divergence axis: density, structure, voice, personality; build 3–5 working candidates behind the floating pill picker) → ensure every variant clears the accessibility floor → user chooses winner for production integration.

4. **Codebase-Wide Motion Health**:
   [Improve Animations](references/emil/improve-animations/overview.md) (run 8-category read-only audit) → prioritize findings by leverage → generate self-contained execution plans under `plans/` → hand off without mutating source unprompted.

## Unified Craft & Engineering Rules

Where Jakub's quality domains and Emil's craft lenses meet, apply these reconciled invariants:

### 1. The Motion Decision Framework

Before writing any motion or evaluating existing motion, answer in order:

1. **Frequency gate**:
   - **100+ times/day** (keyboard shortcuts, command palettes, core tab switches): **No animation. Ever.** Instant state changes only. Raycast has no toggle animation.
   - **Tens of times/day** (hover states, row selection, list navigation): Fast and subtle (under 150ms) or nothing.
   - **Occasional** (modals, drawers, toasts, popovers): Standard animation (150–300ms).
   - **Rare / first-time** (onboarding, success celebrations, empty-state illustrations): Delight budget allowed.
2. **Purpose requirement**: Every animation must serve a clear perceptual purpose:
   - **Feedback** (confirming user action, e.g. press scale)
   - **Spatial consistency** (origin-aware entrance, drawer swipe-to-dismiss)
   - **State indication** (morphing button, accordion expansion)
   - **Preventing jarring changes** (bridging content that would otherwise teleport)
   - **Explanation** (marketing/onboarding product demonstration)
   - **Delight** (strictly limited to rare/first-time moments)
   - *If the only justification is "it looks cool" on a repeated UI element, reject the animation.*
3. **Easing and timing tokens**:
   - Entering / exiting: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1);` (strong ease-out; never `ease-in` on UI).
   - On-screen moving / morphing: `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);`
   - Drawers and bottom sheets: `--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);`
   - Hover / color transitions: `ease` over 100–150ms.
   - Durations: **UI animations stay under 300ms.** Button press: 100–160ms. Tooltips/popovers: 125–200ms. Dropdowns/selects: 150–250ms. Modals/drawers: 200–500ms.
4. **Physicality and origins**:
   - **Never `scale(0)`**: Nothing in the physical world emerges from nothing. Start from `scale(0.95–0.97)` paired with `opacity: 0`.
   - **Origin-aware popovers**: Popovers, tooltips, dropdowns, and context menus must scale from their trigger (`transform-origin: var(--transform-origin)`). Modals are exempt: they center in the viewport and keep `transform-origin: center`.
   - **Button press feedback**: `transform: scale(0.97)` (or `scale-[0.96]`) on `:active` with `transition: transform 160ms ease-out`.
   - **Asymmetric timing**: Slow on deliberate user actions (e.g. hold-to-delete: 2s linear), snappy on system responses (release: 200ms ease-out).
   - **Stagger**: Infrequent entrances stagger 30–80ms between items (or 100ms for semantic hero chunks); never block user interaction during stagger.
   - **Masking crossfades**: When state swaps cross-fade unnaturally, blend with subtle `filter: blur(2px)` (keep blur under 20px).
5. **GPU performance and interruption**:
   - Animate `transform` and `opacity` only (plus `clip-path: inset()` reveals). Never animate layout properties (`width`, `height`, `margin`, `padding`, `top`, `left`).
   - Never use `transition: all`; explicitly name animated properties.
   - In Framer Motion / Motion, use full transform strings (`animate={{ transform: "translateX(100px)" }}`) for hardware acceleration under load.
   - For interruptible UI (toasts, toggles, gestures), use CSS transitions or springs. Keyframes restart from zero when interrupted.
   - Never update parent CSS variables to drive child transforms (causes recalculation storms). Set `transform` on the animated element directly.
6. **Accessibility & touch gating**:
   - Honor `prefers-reduced-motion`: replace movement, scale, and parallax with a short opacity crossfade. Reduced motion means gentler feedback, not zero feedback. For touch gestures (like sheets/drawers), retain direct finger tracking for control while eliminating autonomous post-release bounce or travel.
   - Gate hover styling behind `@media (hover: hover) and (pointer: fine)` so touch taps do not latch sticky hover states. Use `:active` for tactile feedback on touch.
   - On touch platforms, ensure interactive targets meet the 44×44pt (iOS) / 48×48dp (Android) touch target standard (WCAG AA baseline 24×24px).

### 2. Prototyping & Variant Exploration

When building alternative directions for a piece of UI, combine Jakub's structural axes with Emil's craft divergence:
- **Axis of divergence**: Pick one primary axis before coding (Structure, Density, Emphasis, Type scale, Voice, Personality, or Interaction model). State the axis and defend each direction.
- **Unified floor**: Every variant must clear all accessibility and escalation triggers before being placed in the picker (minimum contrast: 4.5:1 normal text, 3:1 large/UI; visible focus; keyboard equivalents). Keyboard navigation, contrast, and focus indicators are non-negotiable.
- **Isolated harness**: Build on the real hosting page or an isolated route (`/prototypes/<slug>`); never mutate production code during exploration. Use a single URL search parameter `?__variant=<name>` as the reload-persistent and shareable source of truth.
- **Harness chrome**: Use the floating dark pill picker from [picker reference](references/variant/picker.md) and [Emil's picker](references/emil/prototype/PICKER.md). Switching is instant without animating the variant change. Keyboard shortcuts (`1–N`, arrows, `R` to replay animation, `H` to hide) must only handle events when focus is in the picker or not trapped in form inputs.

### 3. Adversarial Stress Testing (Break UI)

When checking if a component defends itself against real-world production conditions:
- **Unified harness**: Mount the untouched production component on a throwaway route or single self-contained page in a single column.
- **Schema-backed & hostile catalog**: Combine the scenario cues from [scenarios](references/break/scenarios.md) with the realistic worst-case values from [Emil's catalog](references/emil/break-ui/CATALOG.md) (Aleksandra, long emails, CJK, RTL, diacritics, 0 / 1 / 1,000 items, currencies, dates).
- **Core failure signatures**:
  - Squished icons/avatars: add `flex-shrink: 0`.
  - Unbounded text blowout: add `min-width: 0` on flex children (`minmax(0, 1fr)` in grid).
  - Unbreakable URLs/emails: add `overflow-wrap: anywhere`.
  - Jittery numbers: add `font-variant-numeric: tabular-nums`.
- **Observe before changing**: Inspect at container widths down to 320px and 200% zoom. Report observed breaks by severity before applying fixes.

## Unified Review System

### 1. Scope, Mode & Hand-offs

- **Holistic Screen Review**: Resolves the screen or flow. `quick` mode inspects primary paths (finding cap: 5, HIGH/MEDIUM only); `full` mode inspects all states across all six domains (finding cap: 15).
- **Change Review**: Triggered by branches, PRs, or dirty working trees. Read [upstream.md](upstream.md) and [review-format.md](review-format.md). Expand blast radius up to two hops. Classify findings as `Introduced`, `Regression`, or `Pre-existing`. Only Introduced and Regression count against verdict and cap.
- **Motion Review**: Dedicated motion reviews follow [Review Animations](references/emil/review-animations/overview.md) and use the Before/After/Why table.

### 2. The Six Domains + Motion Craft Order

Inspect in this order so foundational failures are not hidden by polish:

1. [Accessibility](references/accessibility/overview.md) — Operability, WCAG compliance, screen readers, focus rings, semantics.
2. [Layout](references/layout/overview.md) — Spacing, alignment, container adaptivity, reflow at 320px.
3. [Writing](references/writing/overview.md) — Clarity, tone, recovery guidance, punctuation.
4. [Typography](references/typography/overview.md) — Scale, hierarchy, line-height, tabular numbers.
5. [Colors](references/colors/overview.md) — Contrast ratios, palette tokens, semantic color usage.
6. [UI & Motion Polish](references/ui/overview.md) — Concentric radii, surface optical alignment, shadows, and Emil Kowalski's motion standards ([Animate](references/emil/animate/overview.md), [Review Animations](references/emil/review-animations/overview.md)).

### 3. Severity & Non-Negotiable Escalation Triggers

Use one shared severity scale:
- `HIGH`: Blocks task, misleads, causes data loss, or violates an escalation trigger.
- `MEDIUM`: Noticeably harms comprehension, efficiency, or consistency.
- `LOW`: Isolated polish with limited impact (full mode only).

**Automatic HIGH on sight (Escalation Triggers):**
- Interactive control with no accessible name.
- Keyboard-reachable control with no visible focus indicator.
- Pointer-only interactive path with no keyboard alternative.
- Motion or auto-playing media ignoring `prefers-reduced-motion`.
- Content or controls clipped, overlapping, or unreachable at 320px width or 200% zoom.
- Contrast pair failing required WCAG AA ratio.
- State or meaning carried by color alone or by motion alone.
- Destructive action without confirmation, undo, or distinct treatment (safeguards such as typing an identifier must be proportional to irreversible data-loss risk, not mandated for routine actions).
- Truncated content with no way to access the full value.
- `transition: all` or animating layout properties (`width`, `height`, `margin`, `padding`, `top`, `left`).
- `transform: scale(0)` or pure-fade entrance on UI elements.
- `ease-in` timing curve on any UI interaction.
- Animation on keyboard shortcuts, command palettes, or 100+/day high-frequency actions.
- `transform-origin: center` on trigger-anchored popovers, dropdowns, or menus.
- Ungated `:hover` motion causing sticky states on touch devices.

### 4. Remedial Hierarchy

When proposing fixes, prefer earlier solutions over later additions:
1. **Delete**: Remove unneeded motion, redundant separators, or duplicate wrappers.
2. **Use the platform**: Native elements, browser focus rings, native sheet presentations.
3. **Reuse existing tokens**: Existing project curves, spacing steps, and colors before creating new ones.
4. **Correct the value**: Exact easing curve (`--ease-out`), duration, radius, or contrast ratio.
5. **Add**: New tokens, media queries, or explicit ARIA attributes where the platform cannot supply them.

## Review Output Format

Always structure review findings using these exact sections:

### Scope and Coverage
State the mode, exact scope, stack/styling conventions, and coverage across all six domains:

| Domain | Evidence inspected | Result |
| --- | --- | --- |
| Accessibility | `src/Dialog.tsx:42` | Findings count or `Clear` |

### Findings
One table ordered by severity, then reach and leverage. In change reviews, include the `Status` column (`Introduced` / `Regression`):

| # | Severity | Domain | Location | Before | After | Why |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HIGH | Accessibility | `src/Dialog.tsx:42` | `<button><CloseIcon /></button>` | Add `aria-label="Close"` and hide icon | The icon button lacks an accessible name |

### Considered but Rejected
Document 1–3 inspected items in `quick` mode and 2–5 in `full` mode that were deliberately left unchanged:

| Location | Candidate | Rejected because |
| --- | --- | --- |
| `src/Card.tsx:28` | Increase box shadow | Matches shared surface token; altering one breaks consistency |

### Verification
List exact verification commands, browser/screen interactions, and observed results. Separate passed checks from checks marked **Not verified**.

### Verdict
End with exactly one:
- `Block` — One or more `HIGH` findings remain.
- `Needs changes` — Only `MEDIUM` or `LOW` findings remain.
- `Approve` — No actionable findings remain and inspected coverage was verified.
