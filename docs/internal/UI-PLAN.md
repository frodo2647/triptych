# Triptych v2 — UI Plan

## Design Principles

These principles guide all UI additions for v2. They're drawn from research on calm technology, cognitive load theory, progressive disclosure, and patterns from tools like VS Code, Linear, and Jupyter.

### 1. Periphery first, center on demand

Information lives at the edges by default. The user pulls it to center attention when they want it. A status dot changes color (periphery). The user glances at it and sees a one-line label. They click and get full detail. The information never arrives uninvited at the center of attention.

### 2. One primary panel at a time

At any moment, the user's focus is in one panel. The active panel gets full visual presence. Other panels recede slightly. Status indicators are scoped per-panel, not global — the user should never have to figure out "which panel is this notification about?"

### 3. Minimum viable indicator

Before adding any UI element, ask: what is the absolute minimum that conveys this information? Start there. A color change on an existing element is better than a new element. A one-word label is better than a sentence. Add more only when the minimum proves insufficient.

### 4. Frequency determines visibility

Things the user checks constantly stay visible (research phase, verification health). Things checked occasionally hide behind a click (individual claim details, full dependency graph). Things checked rarely live in the terminal or log files.

### 5. Errors are not interruptions — they're state changes

A verification failure is a change in the system's state, not a demand for immediate action. Show it as a persistent state change (status dot turns red, strip tints) rather than a transient alert (popup, toast). The user notices on their next natural glance and decides when to address it.

### 6. Reserve saturated color for meaning

In a dark, muted interface, saturated color is the most powerful attention tool. Every saturated element carries semantic meaning:
- **Green** (#34d399): verified, healthy, active
- **Blue** (#6e73ff): information, links, neutral status
- **Amber** (#fbbf24): pending, needs attention, uncertain
- **Red** (#f87171): failed, error, invalidated

Never use saturated color decoratively.

### 7. Respect working memory

Show summaries, not lists. "4/6 verified, 1 failed" is one chunk. Six individual claim statuses is six chunks. Drill-down exists for when the user wants detail — don't force it on them.

### 8. 2-second glance rule

Every status indicator must be fully understood in under 2 seconds of glance time. If the user needs to read a paragraph to understand the state, the design has failed.

### 9. Theme-ready from day one

All new UI uses CSS custom properties. Dark theme ships first; light theme is a variable swap later. No hardcoded colors in JS.

### 10. Functionality lives inside panels

The shell chrome (topbar, status strips, seams) is for navigation and status. All actual functionality — research state views, verification details, dependency graphs — lives inside the display panel via addons, or in the terminal. The chrome never becomes an app within an app.

---

## What exists today

- **Topbar** (28px): file sidebar toggle, three panel tab buttons with dropdowns, WS connection dot
- **Three panels**: workspace (iframe), display (iframe), terminal (xterm.js)
- **Seams**: draggable dividers between panels
- **File sidebar**: collapsible 140px tree browser
- **Display tab bar**: appears when 2+ output files exist in workspace/output/
- **No notification system, no status indicators, no phase display**

---

## What v2 adds to the UI

### A. Panel status strips

A thin strip (16-20px) at the bottom of each panel. Muted by default — barely visible when everything is healthy. Becomes noticeable only when state changes matter.

**Display panel strip** shows:
- Left: research phase (e.g., "exploring" / "formalizing" / "verifying")
- Right: verification summary (e.g., "3/4 verified" or a colored dot)
- Background tints on error: a subtle red wash when a claim fails

**Workspace panel strip** shows:
- Left: active workspace name
- Right: watcher status dot (green = watching, gray = idle, amber = observation logged)

**Terminal panel strip** shows:
- Left: operation mode (e.g., "autonomous" / "collaborative")  
- Right: nothing normally; shows "verifying..." when agents are running

The strips use the same `--chrome` background as the topbar. Text is `--text-dim` by default, stepping up to `--text-mid` when carrying meaningful state.

### B. Verification state in the display panel

The full research state view (`show_research()`) is already a display addon. What's new:

- **Persistent "Research" tab** in the display panel tab bar when a research state exists. The user can flip between their work output and the research overview without losing either.
- The research tab shows a badge (small dot or count) when verification results are unread.

This means the display panel's file polling needs to also check for `workspace/research/state.md` and offer it as a tab when present.

### C. Toast notifications (confirmations only)

Brief, auto-dismissing (3s) confirmation toasts for user-initiated actions:
- "Research state initialized"
- "Claim C4 emitted"
- "Verification complete: 3 passed"

These appear in a consistent position (bottom-right of the display panel or top-right of the shell). Never more than one at a time. Never for errors — errors are state changes shown in strips.

### D. Watcher indicator

The watcher's observations are logged, not announced. The workspace panel strip shows a small indicator when new watcher observations exist. The user checks when they want.

If the watcher catches a high-confidence error, the workspace strip's dot turns amber and shows a one-line summary on hover. The terminal also gets the full message (the watcher speaks up for clear errors per the skill definition).

---

## Flow walkthroughs

### Flow 1: Human working, AI watching

1. Human draws/writes in workspace. All strips are muted/green. Invisible.
2. Watcher reads snapshots every 30s. Logs observations. Workspace strip dot stays green.
3. Watcher spots possible error. Logs it. Workspace strip dot turns **amber**. No interruption.
4. Human glances at strip, sees amber dot. Hovers: "Possible sign error in line 3". Clicks: terminal shows full observation.
5. Watcher spots definite error. Speaks up in terminal. Workspace strip dot turns **red**.
6. Human reads terminal, fixes error. Strip returns to green.

### Flow 2: AI working autonomously

1. Terminal strip shows "autonomous". Display shows work output.
2. AI emits claims. Display strip shows "formalizing - 2/3 verified". Green dot.
3. Verification failure on claim C3. Display strip tints subtly red. Shows "2/3 verified, 1 failed".
4. Human notices on next glance. Clicks the "Research" tab in display to see full state + graph.
5. AI addresses the failure (logged in attempts). Strip returns to normal. Count updates.
6. Cross-verification at milestone. Display strip shows "cross-verifying...". Returns to "verified" when done.

### Flow 3: Exploration to formalization transition

1. Human is sketching/exploring. No research state exists. Strips are minimal.
2. Watcher detects equations appearing. Logs a "transition" entry.
3. AI prompts in terminal: "What exactly are we trying to show?"
4. Human responds. AI calls `init_research()`.
5. Toast: "Research state initialized". Display panel gains a "Research" tab.
6. Display strip now shows "formalizing - 0 claims". System is active.

### Flow 4: Checking research progress mid-session

1. Human is working in workspace. Display shows a plot from the AI's work.
2. Human clicks "Research" tab in display panel tab bar.
3. Full research state renders: narrative sections + d3 dependency graph.
4. Human reviews, clicks back to the plot tab. No context lost.

---

## What stays in panels (not in chrome)

These live inside display addons / terminal, NOT in the shell chrome:
- Full research state narrative (7 sections)
- Dependency graph visualization
- Individual claim details and verification results
- Watcher observation history
- Verification log contents
- Cross-verification reports

The chrome only shows: phase label, summary counts, colored dots, one-line hover summaries.

---

## Open questions for Quinn

### 1. Status strips: yes/no?

The main UI addition is thin status strips at panel bottoms. They're the least intrusive way to show verification/watcher state without popups or badges in the topbar. But they do add 16-20px of chrome per panel. 

Alternative: put all status info in the topbar (next to existing panel labels). Saves vertical space but makes the topbar busier.

**Preference?**

### 2. Research tab persistence

When research state exists, should the display panel always show a "Research" tab (even if the user hasn't asked for it), or should it only appear when the AI explicitly calls `show_research()`?

Auto-appearing is more discoverable. Manual is less intrusive.

### 3. Toast notifications

Worth adding, or overkill? The terminal already confirms actions via print statements. Toasts would be visible even if the terminal panel is hidden, which is the main argument for them. But they're also another UI system to build and maintain.

### 4. Anything else you want surfaced?

Is there information the current plan doesn't account for? Things you find yourself wanting to see during a session that aren't covered?
