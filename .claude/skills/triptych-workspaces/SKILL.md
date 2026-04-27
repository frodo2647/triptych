---
name: triptych-workspaces
description: Workspace addons for Triptych — HTML files the human works in (whiteboard, PDF viewer, code editor, markdown editor, spreadsheet). Use when asked to create a new workspace tool, switch workspaces, or read what the human is working on via snapshots.
---

# Triptych Workspace Addons

Workspace addons are standalone HTML files in `workspaces/`. They load in the left panel where the human works. The framework auto-discovers new `.html` files and adds them to the workspace dropdown.

## Available workspaces

| Addon | File | Description |
|-------|------|-------------|
| tldraw | `workspaces/tldraw.html` | Drawing/whiteboard canvas. Custom SVG-to-PNG capture. |
| editor | `workspaces/editor.html` | CodeMirror 6 code editor. Python, JS, TS, HTML, CSS, JSON, YAML, LaTeX, SQL, XML, Markdown, Shell. Auto-saves to `workspace/files/`. |
| markdown | `workspaces/markdown.html` | Milkdown WYSIWYG markdown editor with KaTeX math, GFM tables, task lists. Auto-saves. |
| spreadsheet | `workspaces/spreadsheet.html` | jspreadsheet-ce grid. CSV/TSV loading, formulas, dark-themed. Auto-saves. |
| pdf | `workspaces/pdf.html` | Loads PDFs in Chrome's native viewer. Auto-discovers first PDF in `workspace/files/` or opens via `?file=` param. |
| welcome | `workspaces/welcome.html` | Landing screen shown on startup. |

## Workspace commands

Query workspaces from the terminal via `query_workspace('command-name', {params})` or curl.

### editor
| Command | Params | Returns |
|---------|--------|---------|
| `get-content` | — | `{content, fileName, language}` |
| `get-selection` | — | `{selectedText, cursorLine, cursorCol}` |
| `set-content` | `{content}` | `{ok}` |
| `insert-at-cursor` | `{text}` | `{ok}` |
| `replace-selection` | `{text}` | `{ok}` |
| `go-to-line` | `{line}` | `{ok, line}` |
| `open-file` | `{fileName}` | Navigates to file |
| `list-files` | — | `{files: [...]}` (code file extensions) |

### markdown
| Command | Params | Returns |
|---------|--------|---------|
| `get-content` | — | `{markdown, fileName}` |
| `get-selection` | — | `{selectedText}` |
| `set-content` | `{markdown}` | Saves and reloads |
| `open-file` | `{fileName}` | Navigates to file |
| `get-headings` | — | `{headings: [{level, text, line}]}` |
| `list-files` | — | `{files: [...]}` (.md files) |

### spreadsheet
| Command | Params | Returns |
|---------|--------|---------|
| `get-data` | — | `{data, rows, cols}` |
| `get-selection` | — | `{selectedRange}` |
| `set-data` | `{data: [[...]]}` | `{ok}` |
| `set-cell` | `{row, col, value}` | `{ok}` |
| `get-cell` | `{row, col}` | `{value}` |
| `open-file` | `{fileName}` | Navigates to file |
| `export-csv` | — | Saves and returns `{ok, fileName}` |
| `get-summary` | — | `{rows, cols, headers, numericColumns}` |

### pdf
| Command | Params | Returns |
|---------|--------|---------|
| `get-filename` | — | `{fileName}` |

### tldraw
Uses snapshot context (shapes, positions) rather than commands. Read `workspace/snapshots/latest.json`.

## Reading what the human is working on

Workspaces capture screenshots and context every 30 seconds to:
```
workspace/snapshots/latest.png    # Screenshot (read with Read tool)
workspace/snapshots/latest.json   # Context metadata
```

Trigger an instant capture: `curl -s -X POST http://localhost:3000/api/snapshot/now`

All workspaces include `query-context` as a built-in command.

## Building new workspace addons

1. Write an HTML file to `workspaces/my-workspace.html`
2. It auto-appears in the dropdown
3. Include capture.js for snapshot support:

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="/core/theme.css">
  <style>body { margin: 0; background: var(--void); color: var(--text-hi); font-family: var(--font); }</style>
</head>
<body>
  <!-- Your workspace UI -->
  <script src="/core/capture.js"></script>
  <script>
    Capture.init({
      interval: 30000,
      captureImage: async () => {
        // Return base64 PNG string, or omit for default html2canvas
      },
      getContext: () => ({
        // Return metadata object — whatever's useful for Claude
      }),
    });
  </script>
</body>
</html>
```

Load libraries from CDN (`https://esm.sh/package-name`). The framework handles the rest.

After creating a new workspace, update `tools.md` with its description.
