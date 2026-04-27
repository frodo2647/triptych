"""Assumptions display — surface load-bearing assumptions for the human to check.

`show_assumptions` is a thinking-partner primitive: when the work depends on
non-trivial assumptions, render them as a scannable, checkable list rather
than burying them in prose. The human can glance at the panel and catch the
one assumption that's actually wrong before it becomes load-bearing.

Three input shapes are supported:

  - Inline list: pass `assumptions=[{...}, {...}]` for an ad-hoc panel
  - From research state: pass `from_research=True` to pull assumption
    nodes from the dependency graph (`deps.json`). The narrative
    Assumptions section in `state.md` is shown by `show_research`; this
    display surfaces the structured nodes with status badges.
  - Both: inline list extends what's already in the dependency graph

Each assumption is a dict with:
  - `text` (required): the assumption itself, in plain language
  - `status` (optional): one of provisional | observed | verified | invalidated
                          (default: provisional)
  - `why` (optional): one-line note on why we're making it
  - `id` (optional): claim ID or label for cross-reference
"""

import json
import html as html_mod
from pathlib import Path

from ._base import (OUTPUT_DIR, BG_VOID, BG_SURFACE, TEXT_PRIMARY,
                     TEXT_SECONDARY, TEXT_DIM, BORDER, FONT,
                     ACCENT, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
                     ACCENT_YELLOW, atomic_write_text, resolve_display_path)

STATUS_COLORS = {
    'provisional': ACCENT_YELLOW,
    'observed': ACCENT,
    'verified': ACCENT_GREEN,
    'invalidated': ACCENT_RED,
    'unverified': TEXT_DIM,
}

STATUS_LABELS = {
    'provisional': 'provisional',
    'observed': 'observed',
    'verified': 'verified',
    'invalidated': 'invalidated',
    'unverified': 'unverified',
}


def _read_research_assumptions(research_dir):
    """Pull assumption nodes out of the research dependency graph."""
    try:
        from core.research import get_graph
    except ImportError:
        return []
    try:
        graph = get_graph(research_dir)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    out = []
    for node_id, node in graph.get('nodes', {}).items():
        if node.get('type') != 'assumption':
            continue
        out.append({
            'text': node.get('label', node_id),
            'status': node.get('status', 'provisional'),
            'id': node_id,
            'why': '',
        })
    return out


def _normalize(items):
    """Coerce input into the canonical assumption shape."""
    out = []
    for item in items or []:
        if isinstance(item, str):
            out.append({'text': item, 'status': 'provisional', 'why': '', 'id': ''})
            continue
        out.append({
            'text': str(item.get('text', '')).strip(),
            'status': item.get('status', 'provisional'),
            'why': str(item.get('why', '')).strip(),
            'id': str(item.get('id', '')).strip(),
        })
    return [a for a in out if a['text']]


def show_assumptions(assumptions=None, *,
                     title='Assumptions',
                     subtitle=None,
                     from_research=False,
                     research_dir=None,
                     output_dir=None,
                     name='assumptions'):
    """Render an assumptions panel to the display pool.

    Parameters
    ----------
    assumptions : list of dict or str, optional
        Inline assumption list. Each entry can be a string (treated as
        text-only, status=provisional) or a dict with keys
        ``text``, ``status``, ``why``, ``id``.
    title : str
        Panel header.
    subtitle : str, optional
        One-line context under the header (e.g. "for the period derivation").
    from_research : bool
        If True, also pull assumption nodes from the research-state graph.
    research_dir : str or Path, optional
        Override default ``workspace/research/``.
    output_dir : str or Path, optional
        Override default ``workspace/output/``.
    name : str
        Display tab stem. Defaults to ``"assumptions"``.

    Returns
    -------
    str : path to the written HTML file.
    """
    items = []
    if from_research:
        items.extend(_read_research_assumptions(research_dir))
    items.extend(_normalize(assumptions))

    # De-duplicate by (id, text); inline overrides research-state by status.
    seen = {}
    for a in items:
        key = (a.get('id') or '', a['text'])
        seen[key] = a
    items = list(seen.values())

    rows_html = ''
    if not items:
        rows_html = (
            '<div class="empty">'
            'No assumptions registered yet. Add one with '
            '<code>show_assumptions([{"text": "...", "status": "provisional"}])</code> '
            'or via <code>core.research.add_node(id, "assumption", label, status)</code>.'
            '</div>'
        )
    else:
        for a in items:
            status = a['status'] if a['status'] in STATUS_COLORS else 'provisional'
            color = STATUS_COLORS[status]
            label = STATUS_LABELS[status]
            id_chip = ''
            if a['id']:
                id_chip = f'<span class="id-chip">{html_mod.escape(a["id"])}</span>'
            why_block = ''
            if a['why']:
                why_block = f'<div class="why">{html_mod.escape(a["why"])}</div>'
            rows_html += f'''
        <div class="assumption" data-status="{status}">
          <div class="row">
            <span class="status-dot" style="background:{color}"></span>
            <div class="text-col">
              <div class="text">{html_mod.escape(a["text"])}</div>
              {why_block}
            </div>
            <div class="meta">
              {id_chip}
              <span class="status-label" style="color:{color}">{label}</span>
            </div>
          </div>
        </div>'''

    subtitle_html = (
        f'<div class="subtitle">{html_mod.escape(subtitle)}</div>'
        if subtitle else ''
    )

    counts = {}
    for a in items:
        s = a['status'] if a['status'] in STATUS_COLORS else 'provisional'
        counts[s] = counts.get(s, 0) + 1
    chips = ''
    for status in ('provisional', 'observed', 'verified', 'invalidated'):
        if counts.get(status):
            color = STATUS_COLORS[status]
            chips += (
                f'<span class="chip">'
                f'<span class="chip-dot" style="background:{color}"></span>'
                f'<span class="chip-count">{counts[status]}</span>'
                f'<span class="chip-label">{STATUS_LABELS[status]}</span>'
                f'</span>'
            )

    html = f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{html_mod.escape(title)}</title>
<style>
  :root {{
    --void: {BG_VOID};
    --surface: {BG_SURFACE};
    --text: {TEXT_PRIMARY};
    --text-2: {TEXT_SECONDARY};
    --text-3: {TEXT_DIM};
    --border: {BORDER};
    --font: {FONT};
    --radius: 6px;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ scrollbar-color: var(--border) transparent; }}
  body {{
    background: var(--void);
    color: var(--text);
    font-family: var(--font);
    font-size: 13px;
    line-height: 1.55;
    padding: 0;
  }}
  header {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 14px 32px 12px;
    backdrop-filter: blur(8px);
  }}
  .title {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-2);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 2px;
  }}
  .subtitle {{
    color: var(--text-3);
    font-size: 12px;
    margin-bottom: 8px;
  }}
  .summary {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 6px;
  }}
  .chip {{
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 8px;
    border-radius: 3px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    font-size: 11px;
  }}
  .chip-dot {{ width: 6px; height: 6px; border-radius: 50%; }}
  .chip-count {{ color: var(--text); font-weight: 500; }}
  .chip-label {{ color: var(--text-3); }}

  main {{
    padding: 16px 32px 48px;
    max-width: 860px;
  }}
  .assumption {{
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 8px;
    background: var(--surface);
    transition: border-color 0.15s;
  }}
  .assumption:hover {{ border-color: rgba(255,255,255,0.12); }}
  .assumption[data-status="invalidated"] {{ opacity: 0.6; }}
  .row {{
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 11px 14px;
  }}
  .status-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
  }}
  .text-col {{ flex: 1; min-width: 0; }}
  .text {{ color: var(--text); }}
  .why {{
    color: var(--text-3);
    font-size: 11px;
    margin-top: 3px;
    font-style: italic;
  }}
  .meta {{
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }}
  .id-chip {{
    color: var(--text-3);
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    padding: 1px 5px;
    background: rgba(255,255,255,0.03);
    border-radius: 3px;
  }}
  .status-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .empty {{
    color: var(--text-3);
    font-style: italic;
    padding: 28px 0;
    text-align: center;
    font-size: 12px;
  }}
  code {{
    background: rgba(110, 115, 255, 0.1);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.9em;
    color: var(--text-2);
    font-family: 'JetBrains Mono', monospace;
  }}
</style>
</head>
<body>
  <header>
    <div class="title">{html_mod.escape(title)}</div>
    {subtitle_html}
    <div class="summary">{chips}</div>
  </header>
  <main>
    {rows_html}
  </main>
</body></html>'''

    out, effective_filename = resolve_display_path(
        name=name, default_filename='assumptions.html', extension='.html',
        output_dir=output_dir,
    )
    target = out / effective_filename
    atomic_write_text(target, html)
    print(f'[display] Wrote {len(items)} assumption(s) to {effective_filename}')
    return str(target)
