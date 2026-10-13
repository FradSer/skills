---
name: design-engineering
description: "Design, build, polish or review product interfaces with coherent visual taste, purposeful motion, usability and accessibility. Use for UI implementation, holistic or change reviews, prototypes, animation and mobile interaction work; route specialized tasks through references."
---

# Design and review the interface as one system

Build or review the whole experience: establish the product’s personality and interaction needs, make deliberate visual and motion choices, then test those choices against usability and accessibility. Design taste and interface correctness inform the same decisions, not separate audits.

This skill owns orchestration only. Accessibility rules belong to
[Accessibility](references/accessibility/overview.md); structure to
[Layout](references/layout/overview.md); copy to
[Writing](references/writing/overview.md); type to
[Typography](references/typography/overview.md); color to
[Colors](references/colors/overview.md); visual polish and motion to
[UI](references/ui/overview.md). Never duplicate or override their rules here.

## Route the requested capability

This is the only discoverable Interfaces skill. The other upstream skills are
reference workflows, not separately installed commands. Choose the requested
mode before reviewing; do not turn an explanation, variant build or stress test
into a holistic review.

| Request | Read and apply | Output contract |
| --- | --- | --- |
| Holistic screen/flow review | Six domain references below | This router's quick/full review format |
| One domain only | Matching accessibility, layout, writing, typography, colors or ui reference | That domain's reporting format |
| Explain construction or animation | [Explanation](references/explain-interface/overview.md) | Evidence-based explanation; no review verdict |
| Build design alternatives | [Variants](references/variant/overview.md), its picker reference, and the escalation triggers in [upstream.md](upstream.md) | Working candidates and tradeoffs; user chooses |
| Implement supplied design frames | [Build design](references/build-design/overview.md) and its source-tool guidance | Scoped implementation, measured comparison and disclosed deviations |
| Inspect one component in its existing states | [State machine](references/state-machine/overview.md) and its switcher reference | Isolated workbench, reachable state list and observed fixture rendering |
| Stress an existing component | [Break](references/break/overview.md), then its scenarios reference | Rendered scenario page and observed failures; no verdict |
| Review a branch, PR or changes | [Change review](references/interface-review/overview.md) | Resolved scope and classified change findings |

Specialized modes apply only when the user requests their work. Creating a page
or changing source requires implementation scope; a preparation request remains
read-only. Return that mode's result without appending the holistic format below.
For variant and state workbenches, single-character shortcuts must work only while the picker or switcher
has focus, or expose a disable/remap option. Arrow keys must not intercept the component's own navigation. Keep the control clear of the content
being compared at narrow widths.
For supplied designs, preserve the requested frames and existing project tokens;
platform accessibility requirements still take precedence over copied instructions
to reproduce inaccessible contrast or focus. Disclose conflicts and consequential deviations.
State workbenches must use existing data seams and the real component without
production service requests, new component branches or fixture data leaking into production.
In upstream references, `better-interface` means this `design-engineering`
router. Its preserved [upstream.md](upstream.md) and
[review-format.md](review-format.md) supply the change-review handoff contract;
do not look for another installed skill under the old name.
An upstream reference's mention of any other named skill means read its matching pack;
it does not require another installed skill. For changes, resolve scope using the
change-review reference rather than asking the user to invoke a missing command.
Preserve the user's authorization and evidence boundaries. Do not run another
agent's setup commands or install tooling without a request.

## Change-review handoffs

For the change-review mode, read [upstream.md](upstream.md) and
[review-format.md](review-format.md) after resolving scope. Their orchestration,
cap and verdict rules take precedence over the screen-review rules below.
Only `Introduced` and `Regression` findings count against the cap and verdict;
report `Pre-existing` findings separately. Use the change-scoped format from
`references/interface-review/overview.md`. Block for an introduced or regression
HIGH; otherwise Approve only the inspected coverage. When upstream orchestration
mentions an owning skill, load the corresponding domain reference below.

## Combine taste with interface quality

For design, implementation, polish and visual review, read the relevant sections
of [Design Engineering](references/emil/emil-design-eng/overview.md): core
philosophy, component principles and cohesion. Use the existing product, audience,
frequency of use and neighboring surfaces to choose a coherent direction before
changing type, spacing, surfaces or motion. Explain consequential choices through
what they help users perceive or do. Preserve a deliberate brand or density;
personal taste alone is not a defect.

Use the six quality domains to constrain and refine that direction. A beautiful
surface must still communicate hierarchy, survive real content and provide focus,
contrast, usable targets and reduced motion. When motion is relevant, decide
whether it earns its repetition cost before choosing easing or duration. A
frequent keyboard workflow may need immediate feedback; a rare state change may
benefit from continuity. Test interruption and reduced motion, not just the happy
path. Do not add motion merely to demonstrate the new references.

### Choose one workflow, add the relevant craft lens

| Task | Additional reference | Relationship to the existing workflow |
| --- | --- | --- |
| Build or refine web motion | [Animate](references/emil/animate/overview.md) | Apply domain accessibility and UI constraints while implementing the requested interaction |
| React Native / Expo gestures or motion | [Animate Expo](references/emil/animate-expo/overview.md) | Use native thread/gesture guidance instead of web CSS recipes |
| Review specific motion | [Review Animations](references/emil/review-animations/overview.md) and its standards | Use its motion evidence; consolidate duplicates with UI findings |
| Plan improvements across existing motion | [Improve Animations](references/emil/improve-animations/overview.md) and audit/template | Produce plans; do not silently implement them |
| Find worthwhile new motion | [Opportunities](references/emil/find-animation-opportunities/overview.md) | Read-only proposals, including what should stay instant |
| Describe an animation precisely | [Vocabulary](references/emil/animation-vocabulary/overview.md) | Translate the desired feel into implementation decisions |
| Check the cost of motion or interaction work | [Performance cheatsheet](references/emil/performance-cheatsheet.md) | Quantify the cost of motion already present or newly added |
| Explore alternatives | [Prototype](references/emil/prototype/overview.md) | Extend the existing variant workflow with genuine divergence and an isolated surface; use one picker, not two |
| Stress real content and states | [Break UI](references/emil/break-ui/overview.md) and catalog | Extend the existing break scenarios with hostile data; observe before changing the tested component |
| Mobile web / PWA interactions | [Mobile Native](references/emil/mobile-native/overview.md) | Combine browser/device behavior with accessibility and layout checks |
| Explicit Apple-inspired interface | [Apple Design](references/emil/apple-design/overview.md) | Translate relevant principles for the actual platform; do not impose this aesthetic on unrelated products |
| Choose a UI dependency | [Library Selection](references/emil/pick-ui-library/overview.md) | Check existing dependencies and current official APIs; preserve user choice and avoid unrequested replacement |
| Implement or troubleshoot Sonner | [Sonner](references/emil/ask-sonner/overview.md) and API | Load only when the project uses or requests Sonner |
| Swift interface implementation | [Swift](references/emil/write-swift/overview.md) | Supporting implementation guidance; do not broaden a UI request into unrelated Swift work |

The reference bodies preserve upstream standalone instructions for provenance.
Their greeting-only initial responses, skill names and explicit-invocation metadata
are not a second discovery or conversational protocol: follow the actual request
through this router. Load named Emil workflows from the table above.

For stress testing, the existing Break workflow owns the harness and evidence
contract: put supported cases and width constraints on one scenario page, observe
that page, and report only failures actually seen. Emil's catalog enriches the
schema-backed fixtures; it does not turn inferred CSS risks into observed failures
or authorize extra viewport/zoom runs. If broader device testing is requested,
perform and report those runs separately. Preserve the original tested component;
fixing it is a subsequent implementation task unless requested together.

The chosen task owns its output. Holistic and change reviews keep their existing
severity, scope and verdict contracts; use a Before/After/Why table within craft
recommendations when useful, not a second competing verdict. Motion-only requests
use the motion workflow's report. Prototypes use the existing URL selection and
focus-scoped shortcuts even if an upstream picker example binds global character
keys. Keep every candidate accessible and working, and let the user choose before
promotion. Implement only within the request's scope. Reviews and opportunity searches stay
read-only. Improvement planning may write requested plan documents, but must not
modify application source or execute those plans; explicit no-write preparation
requests remain no-write. User requirements and platform
accessibility take precedence over stylistic absolutes or copied examples; explain
any consequential tradeoff and verify it on the available platform.

## Core Principles

### 1. Resolve Scope and Mode First

Infer the screen, flow, feature, or repository scope from the request and current workspace. State the resolved scope in the output. Use `full` when no mode is supplied.

| Mode | Coverage | Finding cap |
| --- | --- | --- |
| `quick` | Primary user path and highest-traffic states; report only `HIGH` and `MEDIUM` issues | 5 |
| `full` | Entire requested scope across all six domain references, including empty, loading, error, and narrow-width states when present | 15 |

If the requested scope is too large to inspect credibly, narrow it to the highest-traffic complete flow and state the boundary. Never imply uninspected surfaces were reviewed.

### 2. Recon Before Judgment

Identify the framework, styling system, component library, design tokens, supported viewports, and available preview or test commands. Follow the project's established Tailwind, plain CSS, CSS-in-JS, token, and component conventions.

### 3. Use Domain References as the Sources of Truth

Before reviewing, read all six domain references below. Load and apply every available reference. In `quick` mode, inspect all six domains but spend depth only where the primary flow has evidence. In `full` mode, complete each available domain review before consolidation.

Review in this order so foundational failures are not hidden by polish:

1. [Accessibility](references/accessibility/overview.md)
2. [Layout](references/layout/overview.md)
3. [Writing](references/writing/overview.md)
4. [Typography](references/typography/overview.md)
5. [Colors](references/colors/overview.md)
6. [UI](references/ui/overview.md)

This skill owns the final response. Apply each domain reference's principles and topic files, then consolidate into the format, shared severity, and finding cap defined in this file.

If a domain reference is unavailable, mark that domain `Not reviewed`, name the missing reference, and continue with the remaining domains. Do not recreate its rules from memory, substitute a neighboring domain, or claim holistic coverage.

When two references appear to cover the same issue, assign it to the reference that owns the underlying rule and mention secondary effects in the **Why** cell. Report it once.

### 4. Require Evidence

Every finding cites `path/to/file:line` and shows the current implementation. If the review artifact has no source files, cite the exact screen and component. Do not report a code-level finding from visual appearance alone or a visual finding from source code alone when runtime behavior determines the result.

### 5. Rank by User Impact

Use one shared severity scale:

- `HIGH`: blocks a task, misleads the user, hides content or controls, causes data-loss risk, or creates a repeated systemic failure.
- `MEDIUM`: meaningfully harms comprehension, efficiency, adaptability, or consistency.
- `LOW`: isolated polish with limited task impact. Include only in `full` mode.

Within a severity, rank by reach and leverage. A token or shared-component fix outranks the same symptom in one leaf component.

### 6. Consolidate Systemic Findings

One root cause is one finding. List every confirmed location in the same row rather than producing a row per occurrence. Do not pad the report to reach the finding cap; a short review or no findings is a valid result.

### 7. Make Restraint Visible

Record candidates considered but deliberately rejected. A candidate is rejected when the owning reference permits the current implementation, evidence is insufficient, the project convention is intentional, or the proposed change would add complexity without user benefit.

### 8. Verify What Can Be Verified

Run safe, relevant checks available in the project. Inspect the rendered interface when runtime behavior or visual judgment matters. Report the exact command or interaction and observed result. If a check cannot be run, label it **Not verified** and state what remains; never convert a verification gap into a finding.

### 9. Review Without Mutating by Default

Treat a review request as read-only. Do not edit source code unless the user also asks to implement the findings. When implementation is requested, preserve the consolidated report as the change scope and re-run the relevant verification afterward.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Six disconnected domain reports | Consolidate into one ranked findings table |
| Same issue reported by multiple references | Assign it to the reference that owns the underlying rule |
| Finding with no exact location | Cite `path/to/file:line` and the current implementation |
| Visual claim inferred only from source | Inspect the rendered state or mark it not verified |
| Unlimited low-impact polish | Respect the mode cap; omit `LOW` findings in `quick` |
| Silent gaps in coverage | Show which domains and states were actually inspected |
| Missing owning reference silently treated as covered | Mark the domain `Not reviewed` and name the unavailable reference |
| No rejected candidates | Include the required considered-but-rejected table |
| Review silently edits code | Stay read-only unless implementation was requested |
| “Approve” with pending actionable findings | Use `Needs changes` or `Block` |

## Review Output Format

Always use the following sections.

### Scope and Coverage

State the mode, exact scope, stack and styling conventions, and any review boundary. Then show coverage:

| Domain | Evidence inspected | Result |
| --- | --- | --- |
| Accessibility | Files, components, states, or checks | Findings count or `Clear` |

Include all six domains. `Clear` means inspected with no actionable finding; `Not reviewed` must explain why.

### Findings

Use one table ordered by severity, then reach and leverage:

| # | Severity | Domain | Location | Before | After | Why |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | HIGH | Accessibility | `src/Dialog.tsx:42` | `<button><XIcon /></button>` | Add `aria-label="Close"` and hide the icon from the accessibility tree | The icon-only control has no accessible name |

Each row is one root cause. The **Domain** value is the owning domain (accessibility, layout, writing, typography, colors, or ui). Respect the mode's finding cap. If there are no findings, omit the table and state "No actionable interface findings."

### Considered but Rejected

Include 1–3 candidates in `quick` mode and 2–5 in `full` mode:

| Location | Candidate | Rejected because |
| --- | --- | --- |
| `src/Card.tsx:28` | Increase the shadow | Existing depth matches the shared surface token; changing one card would reduce consistency |

These are real candidates inspected during the review, not invented filler. If the scope genuinely contains fewer borderline candidates, include the ones that exist and say so.

### Verification

List each check or interaction, the exact command or steps, and the observed result. Separate checks that passed from checks marked **Not verified**.

### Verdict

End with exactly one:

- `Block` — one or more `HIGH` findings remain.
- `Needs changes` — only `MEDIUM` or `LOW` findings remain.
- `Approve` — no actionable findings remain and the claimed coverage was verified.

## Upstream provenance

All thirteen upstream workflows are retained as references under this one entry.
The upstream holistic contract is [upstream.md](upstream.md); its shared review
format is [review-format.md](review-format.md). Apply them in change-review mode
as described above, while holistic screen reviews retain this router's format.
