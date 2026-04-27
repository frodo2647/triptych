"""Research state display addon — renders state.md + dependency graph."""

import json
from pathlib import Path
from collections import Counter

from ._base import (OUTPUT_DIR, BG_VOID, BG_SURFACE, TEXT_PRIMARY,
                     TEXT_SECONDARY, TEXT_DIM, BORDER, FONT,
                     ACCENT, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW,
                     atomic_write_text, resolve_display_path)

STATUS_COLORS = {
    "active": ACCENT_GREEN,
    "verified": ACCENT_BLUE,
    "observed": ACCENT,
    "invalidated": ACCENT_RED,
    "needs-reverification": ACCENT_YELLOW,
    "unverified": TEXT_DIM,
}

STATUS_LABELS = {
    "active": "Active",
    "verified": "Verified",
    "observed": "Observed",
    "invalidated": "Invalidated",
    "needs-reverification": "Needs Re-check",
    "unverified": "Unverified",
}

DEFAULT_COLOR = TEXT_SECONDARY


def _build_summary(graph):
    """Build verification summary counts from the graph."""
    counts = Counter()
    for node in graph["nodes"].values():
        counts[node["status"]] += 1
    return dict(counts)


def show_research(research_dir=None, output_dir=None, name='research'):
    """Render research state + dependency graph to the display panel.

    Writes to `workspace/output/research.html` by default so the display
    gets pinned to tab #2 (see server/index.ts pool sort). Pass `name=None`
    to fall back to `index.html` behavior.
    """
    from core.research import read_state, get_graph, DEFAULT_DIR

    d = research_dir or DEFAULT_DIR
    state_md = read_state(d)
    if state_md is None:
        state_md = "*No research state initialized yet.*"

    try:
        graph = get_graph(d)
    except (FileNotFoundError, json.JSONDecodeError):
        graph = {"nodes": {}, "edges": []}

    graph_json = json.dumps(graph)
    colors_json = json.dumps(STATUS_COLORS)
    labels_json = json.dumps(STATUS_LABELS)

    has_graph = bool(graph["nodes"])
    summary = _build_summary(graph)
    summary_json = json.dumps(summary)
    total_nodes = sum(summary.values())

    html = f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/markdown-it@14/dist/markdown-it.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markdown-it-texmath@1/texmath.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
  :root {{
    --void: {BG_VOID};
    --surface: {BG_SURFACE};
    --text: {TEXT_PRIMARY};
    --text-2: {TEXT_SECONDARY};
    --text-3: {TEXT_DIM};
    --border: {BORDER};
    --blue: {ACCENT_BLUE};
    --green: {ACCENT_GREEN};
    --red: {ACCENT_RED};
    --yellow: {ACCENT_YELLOW};
    --font: {FONT};
    --radius: 6px;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ scrollbar-color: var(--border) transparent; }}
  body {{
    background: var(--void);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.6;
    font-size: 13px;
  }}

  /* ── Summary bar ─────────────────────────────────── */
  .summary-bar {{
    position: sticky;
    top: 0;
    z-index: 10;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 10px 32px;
    display: {"flex" if has_graph else "none"};
    align-items: center;
    gap: 20px;
    font-size: 11px;
    backdrop-filter: blur(8px);
  }}
  .summary-title {{
    color: var(--text-2);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-size: 10px;
    margin-right: 4px;
  }}
  .summary-chips {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .chip {{
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 2px 8px;
    border-radius: 3px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
  }}
  .chip-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .chip-count {{
    color: var(--text);
    font-weight: 500;
  }}
  .chip-label {{
    color: var(--text-3);
  }}

  /* ── Content area ────────────────────────────────── */
  .content {{
    padding: 24px 32px 48px;
    max-width: 860px;
  }}

  /* ── Markdown rendering ──────────────────────────── */
  #narrative h1 {{
    font-size: 20px;
    font-weight: 600;
    color: #e0e0e8;
    margin: 0 0 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }}
  #narrative h2 {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-2);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 28px 0 8px;
  }}
  #narrative h2:first-of-type {{ margin-top: 0; }}
  #narrative p {{ margin: 6px 0; color: var(--text); }}
  #narrative em {{ color: var(--text-3); font-style: italic; }}
  #narrative strong {{ color: #e0e0e8; font-weight: 600; }}
  #narrative ul, #narrative ol {{ padding-left: 20px; margin: 6px 0; }}
  #narrative li {{ margin: 3px 0; }}
  #narrative li::marker {{ color: var(--text-3); }}
  #narrative code {{
    background: rgba(110, 115, 255, 0.1);
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.92em;
    color: var(--blue);
  }}
  #narrative pre {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 14px;
    margin: 10px 0;
    overflow-x: auto;
  }}
  #narrative pre code {{ background: transparent; padding: 0; color: var(--text); }}
  #narrative hr {{ border: none; border-top: 1px solid var(--border); margin: 20px 0; }}
  .katex {{ font-size: 1.05em; }}
  .katex-display {{ margin: 12px 0; }}

  /* ── Graph section ───────────────────────────────── */
  #graph-section {{
    margin-bottom: 32px;
    display: {"block" if has_graph else "none"};
  }}
  .graph-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }}
  .graph-title {{
    font-size: 11px;
    font-weight: 600;
    color: var(--text-2);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  .legend {{
    display: flex;
    gap: 12px;
    font-size: 10px;
    color: var(--text-3);
  }}
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 4px;
  }}
  .legend-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }}
  .legend-diamond {{
    width: 7px;
    height: 7px;
    transform: rotate(45deg);
  }}
  #graph-container {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    position: relative;
  }}

  /* ── Graph SVG ───────────────────────────────────── */
  .graph-link {{
    stroke: var(--border);
    stroke-width: 1.5;
    fill: none;
  }}
  .graph-node {{ cursor: grab; }}
  .graph-node:active {{ cursor: grabbing; }}
  .graph-node text {{
    fill: var(--text-2);
    font-family: var(--font);
    font-size: 10px;
    pointer-events: none;
    user-select: none;
  }}
  .graph-node:hover text {{ fill: var(--text); }}

  /* ── Tooltip ─────────────────────────────────────── */
  .tooltip {{
    position: absolute;
    pointer-events: none;
    background: #1a1a1f;
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 8px 10px;
    font-size: 11px;
    line-height: 1.5;
    color: var(--text);
    max-width: 280px;
    opacity: 0;
    transition: opacity 0.15s;
    z-index: 20;
  }}
  .tooltip.visible {{ opacity: 1; }}
  .tooltip-id {{ color: var(--text-3); font-size: 10px; }}
  .tooltip-label {{ color: var(--text); margin: 2px 0; }}
  .tooltip-status {{ font-size: 10px; }}
</style>
</head>
<body>

  <!-- Summary bar -->
  <div class="summary-bar" id="summary-bar"></div>

  <div class="content">
    <div id="graph-section">
      <div class="graph-header">
        <span class="graph-title">Dependency Graph</span>
        <div class="legend" id="legend"></div>
      </div>
      <div id="graph-container">
        <div class="tooltip" id="tooltip"></div>
      </div>
    </div>

    <div id="narrative"></div>
  </div>

<script>
(function() {{
  var graph = {graph_json};
  var statusColors = {colors_json};
  var statusLabels = {labels_json};
  var summary = {summary_json};
  var defaultColor = "{DEFAULT_COLOR}";

  // ── Summary bar ──────────────────────────────────
  var bar = document.getElementById('summary-bar');
  if (Object.keys(summary).length > 0) {{
    var html = '<span class="summary-title">Status</span><div class="summary-chips">';
    var order = ['verified', 'observed', 'active', 'unverified', 'needs-reverification', 'invalidated'];
    order.forEach(function(s) {{
      if (summary[s]) {{
        var color = statusColors[s] || defaultColor;
        html += '<span class="chip">'
          + '<span class="chip-dot" style="background:' + color + '"></span>'
          + '<span class="chip-count">' + summary[s] + '</span>'
          + '<span class="chip-label">' + (statusLabels[s] || s) + '</span>'
          + '</span>';
      }}
    }});
    html += '</div>';
    bar.innerHTML = html;
  }}

  // ── Markdown narrative ───────────────────────────
  var md = window.markdownit({{ html: false, linkify: true, typographer: true }});
  if (window.texmath && window.katex) {{
    md.use(window.texmath, {{ engine: katex, delimiters: 'dollars' }});
  }}
  document.getElementById('narrative').innerHTML = md.render({state_md!r});

  // ── Legend (only statuses that exist) ─────────────
  var legendEl = document.getElementById('legend');
  var seenStatuses = {{}};
  Object.values(graph.nodes).forEach(function(n) {{ seenStatuses[n.status] = true; }});
  var seenTypes = {{}};
  Object.values(graph.nodes).forEach(function(n) {{ seenTypes[n.type] = true; }});

  var legendHtml = '';
  if (seenTypes['assumption']) {{
    legendHtml += '<span class="legend-item"><span class="legend-diamond" style="background:var(--green)"></span> assumption</span>';
  }}
  if (seenTypes['result']) {{
    legendHtml += '<span class="legend-item"><span class="legend-dot" style="background:var(--blue)"></span> result</span>';
  }}
  legendHtml += '<span style="color:var(--border)">|</span>';
  ['verified','observed','active','unverified','needs-reverification','invalidated'].forEach(function(s) {{
    if (seenStatuses[s]) {{
      var color = statusColors[s] || defaultColor;
      legendHtml += '<span class="legend-item"><span class="legend-dot" style="background:' + color + '"></span> ' + (statusLabels[s] || s).toLowerCase() + '</span>';
    }}
  }});
  legendEl.innerHTML = legendHtml;

  // ── Dependency graph ─────────────────────────────
  var nodeIds = Object.keys(graph.nodes);
  if (nodeIds.length === 0) return;

  var container = document.getElementById('graph-container');
  var W = Math.max(container.clientWidth, 400);
  var H = Math.max(250, Math.min(400, nodeIds.length * 45));
  container.style.height = H + 'px';

  var svg = d3.select(container).append('svg')
    .attr('width', '100%').attr('height', '100%')
    .attr('viewBox', '0 0 ' + W + ' ' + H);

  // Build data
  var nodes = nodeIds.map(function(id) {{
    var n = graph.nodes[id];
    return {{ id: id, label: n.label, type: n.type, status: n.status }};
  }});
  var nodeIndex = {{}};
  nodes.forEach(function(n, i) {{ nodeIndex[n.id] = i; }});
  var links = graph.edges.filter(function(e) {{
    return nodeIndex[e.from] !== undefined && nodeIndex[e.to] !== undefined;
  }}).map(function(e) {{
    return {{ source: nodeIndex[e.from], target: nodeIndex[e.to] }};
  }});

  // Arrow marker
  svg.append('defs').append('marker')
    .attr('id', 'arrow').attr('viewBox', '0 -3 6 6')
    .attr('refX', 16).attr('refY', 0)
    .attr('markerWidth', 5).attr('markerHeight', 5)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-3L6,0L0,3')
    .attr('fill', '{BORDER}');

  // Simulation
  var pad = 40;
  var sim = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).distance(80).strength(0.8))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide().radius(30))
    .force('x', d3.forceX(W / 2).strength(0.08))
    .force('y', d3.forceY(H / 2).strength(0.08));

  // Links
  var link = svg.selectAll('.graph-link').data(links).enter().append('line')
    .attr('class', 'graph-link')
    .attr('marker-end', 'url(#arrow)');

  // Node groups
  var node = svg.selectAll('.graph-node').data(nodes).enter().append('g')
    .attr('class', 'graph-node');

  // Shape: diamond for assumptions, circle for results
  node.each(function(d) {{
    var el = d3.select(this);
    var color = statusColors[d.status] || defaultColor;
    if (d.type === 'assumption') {{
      el.append('rect')
        .attr('width', 10).attr('height', 10)
        .attr('x', -5).attr('y', -5)
        .attr('transform', 'rotate(45)')
        .attr('fill', color)
        .attr('rx', 1);
    }} else {{
      el.append('circle')
        .attr('r', 6)
        .attr('fill', color);
    }}
  }});

  // Labels
  node.append('text')
    .attr('dx', 12).attr('dy', 3.5)
    .text(function(d) {{ return d.id; }});

  // Tooltip
  var tooltip = document.getElementById('tooltip');
  node.on('mouseenter', function(event, d) {{
    var color = statusColors[d.status] || defaultColor;
    tooltip.innerHTML =
      '<div class="tooltip-id">' + d.id + ' &middot; ' + d.type + '</div>'
      + '<div class="tooltip-label">' + d.label + '</div>'
      + '<div class="tooltip-status" style="color:' + color + '">' + (statusLabels[d.status] || d.status) + '</div>';
    tooltip.classList.add('visible');
  }}).on('mousemove', function(event) {{
    var rect = container.getBoundingClientRect();
    tooltip.style.left = (event.clientX - rect.left + 12) + 'px';
    tooltip.style.top = (event.clientY - rect.top - 10) + 'px';
  }}).on('mouseleave', function() {{
    tooltip.classList.remove('visible');
  }});

  // Drag
  node.call(d3.drag()
    .on('start', function(event, d) {{
      if (!event.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }})
    .on('drag', function(event, d) {{ d.fx = event.x; d.fy = event.y; }})
    .on('end', function(event, d) {{
      if (!event.active) sim.alphaTarget(0);
      d.fx = null; d.fy = null;
    }}));

  // Tick
  sim.on('tick', function() {{
    // Keep nodes in bounds
    nodes.forEach(function(d) {{
      d.x = Math.max(pad, Math.min(W - pad, d.x));
      d.y = Math.max(pad, Math.min(H - pad, d.y));
    }});
    link
      .attr('x1', function(d) {{ return d.source.x; }})
      .attr('y1', function(d) {{ return d.source.y; }})
      .attr('x2', function(d) {{ return d.target.x; }})
      .attr('y2', function(d) {{ return d.target.y; }});
    node.attr('transform', function(d) {{ return 'translate(' + d.x + ',' + d.y + ')'; }});
  }});
}})();
</script>
</body></html>'''

    out, effective_filename = resolve_display_path(
        name=name, default_filename='index.html', extension='.html',
        output_dir=output_dir,
    )
    atomic_write_text(out / effective_filename, html)
    print(f'[display] Wrote research state to {effective_filename}')
