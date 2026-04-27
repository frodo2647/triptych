# Multi-Instance Panels (Deferred)

## Why deferred

Decided 2026-03-15 to defer until after core viewers are built and the end-to-end flow is proven.

The thesis of Triptych is "the simple thing that works." Multi-instance adds framework complexity before we've tested the product with real viewers (tldraw, PDF, code editor). The current single-instance model handles all immediate use cases (multi-device via URL params, panel toggle via tab buttons). Build the viewers, prove the core loop (draw -> snapshot -> Claude sees -> Claude outputs -> display reloads), then revisit.

The refactor won't be meaningfully harder later -- the panel data model is clean and the session concept slots in naturally.

## What it would add

- Multiple panels of the same type (e.g., two workspaces side by side)
- "Sessions" -- each Claude PTY + its own output dir, multiple panels can bind to one session
- Plus button with dropdown to add new W/D/T or show hidden panels
- Drag-to-reorder tabs
- Cross-tab layout cloning via localStorage

## Architecture (when we build it)

### Panel instances
Each panel gets a unique ID:
```
{ id: 'w1', type: 'workspace', sessionId: 'session-1', viewerId: 'welcome' }
{ id: 'd1', type: 'display', sessionId: 'session-1' }
{ id: 't1', type: 'terminal', sessionId: 'session-1' }
```

### Sessions
A "session" is a Claude Code PTY + its associated output directory:
```
session-1:
  PTY: claude --dangerously-skip-permissions
  output: workspace/output/session-1/
  snapshots: workspace/snapshots/session-1/
```

### Server changes needed
- Replace singleton `ptyProcess` with `sessions` Map
- Add `GET /api/sessions`, `POST /api/sessions` endpoints
- Snapshot endpoint takes session ID
- Per-session output dirs + file watchers

### Client changes needed
- Layout stored as dynamic array of panel descriptors (not 3 fixed DOM elements)
- Tab bar dynamically creates/removes buttons
- Plus button dropdown
- localStorage persistence for cross-tab cloning

### Implementation estimate
Moderate overhaul (~2-3 hours). Touches server/index.ts, shell.html, shell.css, shell.js, capture.js.
