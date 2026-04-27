---
name: display-craft
description: Visual quality rubric for Triptych display tabs — panel-size constraints (800–1200px), dark theme alignment, hierarchy in a narrow panel, named tabs, "live" vs "dead" displays. Use during the polish pass of a new display, when a display feels off but you can't say why, or when a tool's UI is fighting the panel size. Distinct from /display-design-workflow (the build flow); applies during steps 4 and 6.
---

# Display Craft

The display panel is narrow (800–1200px), dark-themed, and lives next to a
human's workspace. A display works when the human glances at it and
immediately sees what's happening; it fails when they have to lean in.
This rubric makes displays land the first way.

## When to use

- Step 4 ("test under update pressure") of `/display-design-workflow`
- Step 6 ("clean up") of the same workflow
- A display feels off and you can't say why
- A tool you're considering for embed has CSS resisting the panel size —
  `/integration-design` will route you here

## The rubric

### 1. Panel size — work at 800px, design at 1000px

Open the display at 800px wide before declaring done. Horizontal scroll
means the layout broke. **Anti-pattern: `min-width: 1400px` clamps.**
That's the display saying it doesn't want to live in a panel — make it
`ExternalTool` (see `/integration-design`) or redesign.

Wide tables overflow first; convert to two-column key/value or split.

### 2. Theme — content controls its own when the medium calls for it

`core/theme.css` provides dark tokens for prose, panels, code, links.
**Inherit by default.** Override only when content has its own medium:
matplotlib uses matplotlib's theme, three.js picks its own background,
LaTeX uses the latex display's tokens. Don't force dark CSS over content
with its own look — muddy contrast.

### 3. Hierarchy — one focal element, ≤ 3 type sizes

In a narrow panel, the eye lands on one thing. Pick what it is — a
number, a chart, a status — and make everything else smaller and quieter.
Three type sizes is the ceiling: title, body, caption.

### 4. Live, not dead

Every display the agent ships should answer one of:

- What is the current state?
- What just happened?
- What's the agent doing?

A display sitting unchanged from 20 minutes ago is dead weight. Prune
with `cleanup_displays`.

### 5. Named tabs survive — anonymous tabs are scratch

`name="training"` writes to `training.html` and survives
`cleanup_displays(keep=[...])`. `name=None` writes to `index.html` and
gets overwritten on the next anonymous call. Use named for anything
coexisting with others; anonymous for the single scratch slot. **Three
displays named `*_v2`, `*_push`, `*_old` is iteration residue** — prune.

### 6. Re-use primitives, don't invent

Reach for `displays/_page.py`'s `render_page`, `displays/matplotlib.py`,
`displays/plotly.py`, `displays/_graph.py`, `core/theme.css` tokens
before custom CSS. A one-off color is fine until three displays have
three slightly different accent blues.

## Mentor mode

When reviewing a display the user built, name the rubric items it hits
and the ones it misses. Don't rewrite unless asked — the craft is in the
*seeing*, and pointing is more durable than fixing.

## Related

- `/display-design-workflow` — the six-step build flow this rubric plugs into
- `/integration-design` — when craft issues say "this should be External"
- `/critique`, `/polish`, `/typeset`, `/layout` — drop in for specific
  polish passes; general design rubric, this is the Triptych-panel one
- `core/theme.css`, `displays/_page.py` — primitives to reuse
