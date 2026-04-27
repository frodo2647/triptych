---
name: display-design-workflow
description: Six-step workflow for designing a new display or iterating on an existing one — scope, sketch, wire data, test under update pressure, register, clean up. Use when building a new display addon, polishing a one-off visualization, or the output pool has started accumulating iteration residue.
---

# Display Design Workflow

Triptych displays are easy to produce and easy to leave as drift. The default
pattern — "write HTML, see what sticks" — leaves the output pool full of
stage-6, stage-6-v2, stage-6-push residue. This skill turns that pattern
into six explicit checkpoints so each display lands intentional.

Use this skill whenever you're:
- Adding a new display addon under `displays/`
- Authoring a one-off visualization (named tab) that will live for a while
- Polishing an existing display that has grown organically

## The six steps

### 1. Scope

Before writing anything, answer four questions:

- **What data drives this?** One dataset? Multiple streams joined?
  (If joined, sketch the join on paper or in scratch — don't discover it
  mid-implementation.)
- **What's the update cadence?** Live (every N seconds during a run),
  incremental (appended as results land), or one-shot (write once, never
  update)?
- **Live or one-shot?** Live displays need `atomic_write_text` + a stable
  tab stem so the user doesn't lose their selection on each rewrite. One-shot
  can just write HTML and forget.
- **Who reads this?** You (agent reading back your own progress), Quinn
  (narrative), or a future session (archival)? Audience changes density.

Write a one-line "This display shows X from Y, updated Z, for W" before
proceeding.

### 2. Sketch with dummy data

Build the HTML with fake but realistic-shaped data first. This catches
layout problems (legend overflows, tab bar truncation, fonts too small)
without the overhead of wiring a live feed.

Reuse existing primitives:
- `displays/_page.py`'s `write_page` / `render_page` for the page shell
- `core/theme.css` tokens for colors, spacing, fonts — no one-off palettes
- `displays/_graph.py` (if dependency-graph-shaped), `displays/matplotlib.py`
  (static), `displays/plotly.py` (interactive)

If you're reaching for custom CSS, pause. The theme has an answer 90% of the
time; a one-off color feels fine until three displays have three slightly
different accent blues.

### 3. Wire the real data

Replace the dummy with the actual source. Handle these explicitly:

- **Empty state.** What renders when the dataset is empty? ("No results yet"
  beats a blank panel.)
- **Growing state.** What renders when results are incomplete? Show what
  exists + a subtle "in progress" marker.
- **Error state.** If the data read throws, what does the user see?

If any of these requires more than 5 lines of code, reconsider whether this
display is the right shape — maybe it should be split into two tabs, or
summarized differently.

### 4. Test under update pressure

Apply the visual rubric from `/display-craft` here — panel-size check at
800px, theme inheritance, hierarchy, named tabs. If it doesn't pass, the
display isn't done yet.



For live displays, simulate the update cadence:

- Write the data file in a loop, say every 2 seconds for 30 seconds.
- Watch the display panel. Does the tab selection survive? Does content
  flicker? Does the iframe scroll position reset?
- If flicker: check `atomic_write_text` is being used. Check the tab stem
  is stable (not drifting between `training` and `training-v2`).
- If scroll resets: the iframe `src` shouldn't change — only the file's
  `mtime`. The default display panel already cache-busts by mtime.

Skip this step only for one-shot displays. For anything live, skipping
here is what creates "the agent did some work, the display panel got
weird, I don't know what changed" — the experience Trial 1 flagged.

### 5. Register (named vs. anonymous)

Decide:

- **Anonymous** (`name=None` → `index.html`). Appropriate for the single
  "what am I showing right now" tab. One per call — new anonymous calls
  overwrite.
- **Named** (`name="training"` → `training.html`). Appropriate when the
  display should coexist with others, survive reloads, or be linked by
  a permanent tab number. Multiple names = multiple tabs.

If named and persistent, register in `tools.md` under "Display Addons" so
future sessions can discover it without reading the source.

Commit conventions:
- Code change: conventional commit, one per addon
- `tools.md` update: same commit as the code that introduces the addon

### 6. Clean up iteration artifacts

Before moving on, inspect `workspace/output/`:

```python
import sys; sys.path.insert(0, '.')
from pathlib import Path
print([f.name for f in Path('workspace/output').iterdir() if f.is_file()])
```

If there are stems from intermediate iterations you don't need anymore,
call `cleanup_displays(keep=[...])` to prune them. Specifically look for:

- `*_v2`, `*_push`, `*_old` — naming patterns that indicate iteration residue
- `.py` files in `workspace/output/` — source code belongs in `scripts/`,
  not the display pool
- Duplicate history dashboards (`mnist-history.html` + `emnist-history.html`
  with identical structure — consolidate into one)

`workspace/output/` is the display pool, not a scratch directory. When in
doubt: render + summarize? Or render + trim? Err toward trim.

## Quick reference

| Step | One-liner |
|------|-----------|
| 1. Scope | "Shows X from Y, updated Z, for audience W" |
| 2. Sketch | Dummy data, reuse primitives, no one-off CSS |
| 3. Wire | Handle empty, growing, and error states explicitly |
| 4. Pressure-test | Simulate updates; watch for flicker + scroll reset |
| 5. Register | Named vs anonymous; if named + persistent, add to tools.md |
| 6. Clean up | Prune residue with `cleanup_displays(keep=[...])` |

## Related skills

- `/triptych-displays` — catalog of existing display types
- `/display-craft` — visual quality rubric applied at steps 4 and 6
- `/integration-design` — embed-vs-external for third-party tools (different
  question: "do I display this at all, or link out?")
