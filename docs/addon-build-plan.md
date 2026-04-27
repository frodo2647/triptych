# Plan: Core Addons + File Sidebar + Command Infrastructure

## Context
Building the general-purpose addons Triptych needs for research. Reuse existing tools wherever possible (PDF.js, CodeMirror 6, Milkdown, jspreadsheet-ce). Addons expose bidirectional tools so Claude can query workspace state and send commands.

Also adding: file sidebar (shell framework change) and command/query infrastructure (minimal WS extension).

---

## Phase 0A: File Sidebar (framework — `core/`)

Collapsible sidebar on the left edge of the shell, always accessible. Click a file → opens in the appropriate workspace addon.

### Server addition: `/api/browse` — `server/index.ts`
- `GET /api/browse/*` — returns `{ type: 'dir', entries: [{name, type, size, ext}] }` for directories
- Path traversal protection (same pattern as `/api/files`)
- Scoped to `workspace/files/` directory (user's shared files)
- ~15 lines

### Shell changes — `core/shell.html` + `core/shell.js` + `core/shell.css`
- Add sidebar `<div>` to shell.html (left of workspace panel)
- Toggle button in topbar (or collapse handle on sidebar edge)
- `shell.js`: fetch `/api/browse/` recursively, render `<ul>` tree
- Click handler: map file extension → workspace addon:
  - `.pdf` → `loadWorkspace('pdf')`
  - `.md` → `loadWorkspace('markdown')`
  - `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.html`, `.css`, `.tex` → `loadWorkspace('editor')`
  - `.csv`, `.tsv` → `loadWorkspace('spreadsheet')`
  - images → display directly
- Pass selected filename to workspace via URL param or WS message
- Expand/collapse folders, file type icons (CSS/emoji)
- Drag-and-drop upload zone (HTML5 File API → PUT `/api/files/`)
- ~200 lines JS, ~50 lines CSS

### Files:
- Edit: `server/index.ts` (add `/api/browse` endpoint)
- Edit: `core/shell.html` (add sidebar div)
- Edit: `core/shell.js` (add sidebar logic, file-to-workspace mapping)
- Edit: `core/shell.css` (sidebar styling)

---

## Phase 0B: Command Infrastructure (framework — minimal)

### Server: WS message routing — `server/index.ts`
- Add `case 'workspace-command':` to WS switch — broadcasts to viewer role (~3 lines)
- Add `case 'command-response':` — routes response back to requesting client (~5 lines)
- Add `POST /api/workspace/command` — HTTP endpoint so Claude can send commands via curl. Server sends WS command, waits for response (with timeout), returns via HTTP response. (~20 lines)

### Capture.js: command handler — `core/capture.js`
- Add `Capture.registerCommands(handlers)` — stores handler map
- In existing `_ws.onmessage`, add `workspace-command` handling — calls handler, sends `command-response` back via WS (~20 lines)
- Built-in command: `query-context` (returns current getContext() data)

### Python helper — `displays/_command.py`
- `query_workspace(command, params={}, timeout=2.0)` — HTTP POST to `/api/workspace/command`, returns JSON response
- Used by Claude: `from displays._command import query_workspace`
- No WebSocket dependency — uses HTTP via `urllib` (~30 lines)

### Files:
- Edit: `server/index.ts` (~25 lines added)
- Edit: `core/capture.js` (~20 lines added)
- Create: `displays/_command.py` (~30 lines)
- Edit: `displays/__init__.py` (export `query_workspace`)

---

## Phase 1: PDF Workspace + Display

**Workspace: `workspaces/pdf.html`** — Wrap PDF.js viewer
- Load PDF.js from CDN (pdfjs-dist + viewer)
- Use PDF.js's built-in viewer UI — don't build custom controls
- Integrate with capture.js for snapshots
- Accept filename via URL param from file sidebar: `pdf.html?file=paper.pdf`
- Load files from `/api/files/` endpoint

**Registered commands:**
- `get-selection` → `{ selectedText, page }`
- `get-page-text` → `{ text, page }`
- `get-document-text` → `{ text, totalPages, fileName }`
- `go-to-page` → navigate to page N
- `search-text` → `{ query }` → `{ matches: [{page, snippet}] }`
- `get-outline` → document TOC

**Context schema:** `{ workspace: "pdf", fileName, page, totalPages, selectedText }`

**Display: `displays/pdf.py`**
- `show_pdf(path_or_bytes, filename='output.pdf')` — write PDF to output dir
- Update `core/default-display.html` to detect + embed `.pdf` files

### Files:
- Create: `workspaces/pdf.html`
- Create: `displays/pdf.py`
- Edit: `displays/__init__.py`
- Edit: `core/default-display.html` (PDF detection)
- Edit: `tools.md`

---

## Phase 2: Markdown Workspace + Display

**Workspace: `workspaces/markdown.html`** — Milkdown WYSIWYG editor
- Milkdown from esm.sh — inline rendering as you type (Obsidian-style)
- KaTeX plugin for math blocks
- Syntax highlighting for code blocks
- Auto-save to `workspace/files/{fileName}` on every change (debounced 1s)
- Accept filename via URL param from file sidebar
- Dark theme: style ProseMirror nodes with Triptych palette

**Registered commands:**
- `get-content` → `{ markdown, fileName }`
- `get-selection` → `{ selectedText, cursorLine }`
- `set-content` → replace document
- `insert-at-cursor` → insert text
- `replace-selection` → replace selected text
- `open-file` → load from `workspace/files/`
- `get-headings` → document outline

**Context schema:** `{ workspace: "markdown", fileName, content, selectedText, cursorLine, wordCount }`

**Display: `displays/markdown.py`**
- `show_markdown(md_string, filename='index.html', title=None)`
- Generates HTML with markdown-it + KaTeX from CDN (client-side rendering)
- Dark theme

### Files:
- Create: `workspaces/markdown.html`
- Create: `displays/markdown.py`
- Edit: `displays/__init__.py`
- Edit: `tools.md`
- Create: `.claude/skills/triptych-markdown/SKILL.md`

---

## Phase 3: Code Editor Workspace + Display

**Workspace: `workspaces/editor.html`** — CodeMirror 6
- CodeMirror 6 from esm.sh
- Language modes: Python, JS/TS, HTML, CSS, JSON, LaTeX, YAML
- Auto-detect language from file extension
- Auto-save (debounced 1s)
- Accept filename via URL param from file sidebar

**Registered commands:**
- `get-content` → `{ content, fileName, language }`
- `get-selection` → `{ selectedText, cursorLine, cursorCol }`
- `set-content` → replace file
- `insert-at-cursor` → insert text
- `replace-selection` → replace selected text
- `go-to-line` → jump to line N
- `open-file` → load from `workspace/files/`

**Context schema:** `{ workspace: "editor", fileName, language, content, selectedText, cursorLine }`

**Display: `displays/code.py`**
- `show_code(code, language='python', filename='index.html', title=None)` — syntax highlighted via Prism.js CDN
- `show_diff(old, new, language='python')` — side-by-side diff view

### Files:
- Create: `workspaces/editor.html`
- Create: `displays/code.py`
- Edit: `displays/__init__.py`
- Edit: `tools.md`

---

## Phase 4: Spreadsheet Workspace + Display

**Workspace: `workspaces/spreadsheet.html`** — jspreadsheet-ce
- jspreadsheet-ce from CDN (MIT)
- Load CSV/TSV/JSON from `workspace/files/`
- Basic formulas, cell formatting
- Auto-save (debounced 2s)
- Accept filename via URL param from file sidebar

**Registered commands:**
- `get-data` → `{ data: [[...]], headers, rows, cols }`
- `get-selection` → `{ selectedRange, selectedData }`
- `set-data` → replace spreadsheet
- `set-cell` → `{ row, col, value }`
- `open-file` → load CSV from `workspace/files/`
- `export-csv` → save to `workspace/files/`
- `get-summary` → quick data profile

**Context schema:** `{ workspace: "spreadsheet", fileName, rows, cols, selectedRange, selectedData }`

**Display: `displays/table.py`**
- `show_table(data, columns=None, filename='index.html', title=None)` — dark HTML table, sortable
- Accepts: list of dicts, list of lists, pandas DataFrame
- `show_dataframe(df, title=None)` — pandas shortcut

### Files:
- Create: `workspaces/spreadsheet.html`
- Create: `displays/table.py`
- Edit: `displays/__init__.py`
- Edit: `tools.md`

---

## Phase 5: D3 Display

**Display: `displays/d3.py`** — no workspace needed
- `show_d3(js_code, data=None, width=800, height=600, filename='index.html')`
- `d3_scaffold(body_js, width, height)` — generates HTML boilerplate: D3 v7 from CDN, SVG, dark theme
- Embeds data as JSON for D3 code to reference

### Files:
- Create: `displays/d3.py`
- Edit: `displays/__init__.py`
- Edit: `tools.md`

---

## Verification per phase

### Phase 0A (File sidebar)
- Sidebar renders file tree from `workspace/files/`
- Click `.md` file → switches to markdown workspace with that file loaded
- Drag-drop upload works
- Collapse/expand works

### Phase 0B (Commands)
- `curl -X POST http://localhost:3000/api/workspace/command -H 'Content-Type: application/json' -d '{"command":"query-context"}'` returns context
- `python -c "from displays._command import query_workspace; print(query_workspace('query-context'))"` works
- `npm test` passes (add command routing tests)

### Phases 1-5 (each addon)
- Workspace loads without console errors
- All registered commands respond correctly via curl
- Display addon writes correct output
- Auto-save updates `workspace/files/` on change
- File sidebar opens files in the correct workspace
- `npm test` passes

---

## Summary of simplifications

| Decision | Why |
|----------|-----|
| PDF.js viewer as-is | Don't build what already exists |
| Milkdown for markdown | WYSIWYG inline rendering, Obsidian-style |
| CodeMirror 6 for code | Lightweight, modular, CDN-friendly |
| jspreadsheet-ce for spreadsheet | Ready-made, MIT, just load it |
| Vanilla JS file tree | ~200 lines, simpler than any library |
| HTTP command API | Claude uses curl/Python, no WS dependency in Python |
| URL params for file passing | Sidebar → workspace via `?file=name.pdf`, simple |
