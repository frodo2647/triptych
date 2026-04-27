"""AutoResearch display addon — experiment progress dashboard.

Reads structured attempts from `attempts.jsonl` (written by
`core.research.add_attempt`) — does not scrape the rendered markdown.
"""

import html as html_mod
import json
import re
from pathlib import Path

from ._base import (OUTPUT_DIR, BG_VOID, BG_SURFACE, TEXT_PRIMARY,
                     TEXT_SECONDARY, TEXT_DIM, BORDER, FONT,
                     ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED, ACCENT_YELLOW,
                     atomic_write_text, resolve_display_path)


def _parse_goal(state_text):
    """Extract goal from state.md. Returns '' if no state or section."""
    if not state_text:
        return ''
    match = re.search(r'## Goal\s*\n(.*?)(?=\n## |\Z)', state_text, re.DOTALL)
    return match.group(1).strip() if match else ''


def show_autoresearch(research_dir=None, output_dir=None, filename='index.html',
                      name=None, display_id=None, title=None):
    """Render autoresearch experiment dashboard.

    Reads `attempts.jsonl` and `state.md` from the research directory.
    Pass `name=` to coexist with other displays as a named tab.
    """
    from core.research import read_state, read_attempts, DEFAULT_DIR

    d = research_dir or DEFAULT_DIR
    state_text = read_state(d)
    attempts = read_attempts(d)
    goal = _parse_goal(state_text)

    total = len(attempts)
    kept = sum(1 for a in attempts if a.get('outcome') == 'kept')
    reverted = sum(1 for a in attempts if a.get('outcome') == 'reverted')

    metric_series = []
    best_val = None
    for i, a in enumerate(attempts):
        new_val = a.get('new_val')
        if new_val is None:
            continue
        metric_series.append({
            'i': i + 1,
            'val': new_val,
            'outcome': a.get('outcome', 'unknown'),
            'desc': a.get('description', ''),
        })
        if a.get('outcome') == 'kept':
            if best_val is None or new_val < best_val:
                best_val = new_val

    baseline = attempts[0].get('old_val') if attempts else None

    attempts_json = json.dumps(attempts)
    series_json = json.dumps(metric_series)
    title_html = (
        f'<div class="tp-title">{html_mod.escape(title)}</div>' if title else ''
    )

    html = f'''<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --void: {BG_VOID}; --surface: {BG_SURFACE}; --text: {TEXT_PRIMARY};
    --text-2: {TEXT_SECONDARY}; --text-3: {TEXT_DIM}; --border: {BORDER};
    --blue: {ACCENT_BLUE}; --green: {ACCENT_GREEN};
    --red: {ACCENT_RED}; --yellow: {ACCENT_YELLOW};
    --font: {FONT}; --radius: 6px;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html {{ scrollbar-color: var(--border) transparent; }}
  body {{
    background: var(--void); color: var(--text);
    font-family: var(--font); font-size: 13px; line-height: 1.6;
  }}

  .header {{
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
  }}
  .header-title {{
    font-size: 11px; font-weight: 600; color: var(--text-2);
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px;
  }}
  .header-goal {{ color: var(--text); font-size: 14px; }}
  .tp-title {{
    font-size: 12px; color: var(--text-2);
    letter-spacing: 0.05em; padding: 18px 24px 0;
  }}

  .stats {{
    display: flex; gap: 12px; padding: 16px 24px; flex-wrap: wrap;
  }}
  .stat {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 12px 16px;
    flex: 1; min-width: 100px; text-align: center;
  }}
  .stat-value {{ font-size: 24px; font-weight: 600; line-height: 1.2; }}
  .stat-label {{
    font-size: 10px; color: var(--text-3); text-transform: uppercase;
    letter-spacing: 0.06em; margin-top: 2px;
  }}

  .chart-container {{
    margin: 0 24px; padding: 16px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius);
  }}
  .chart-title {{
    font-size: 11px; font-weight: 600; color: var(--text-2);
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px;
  }}
  canvas {{ max-height: 250px; }}

  .log {{ margin: 16px 24px 32px; padding: 0; }}
  .log-title {{
    font-size: 11px; font-weight: 600; color: var(--text-2);
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;
  }}
  .log-entry {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 8px 12px; border-bottom: 1px solid var(--border);
    font-size: 12px;
  }}
  .log-entry:last-child {{ border-bottom: none; }}
  .log-num {{
    color: var(--text-3); font-size: 10px; min-width: 24px;
    text-align: right; padding-top: 1px;
  }}
  .log-badge {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.04em; padding: 2px 6px; border-radius: 3px;
    min-width: 56px; text-align: center; flex-shrink: 0;
  }}
  .badge-kept {{ background: rgba(52,211,153,0.12); color: var(--green); }}
  .badge-reverted {{ background: rgba(248,113,113,0.12); color: var(--red); }}
  .badge-pending {{ background: rgba(251,191,36,0.12); color: var(--yellow); }}
  .badge-unknown {{ background: rgba(85,85,96,0.12); color: var(--text-3); }}
  .log-desc {{ color: var(--text); flex: 1; }}
  .log-metric {{ color: var(--text-2); font-size: 11px; white-space: nowrap; }}

  .empty-state {{
    text-align: center; color: var(--text-3); padding: 60px 24px;
    font-size: 14px;
  }}
  .empty-hint {{ font-size: 12px; margin-top: 8px; color: var(--text-3); opacity: 0.6; }}
</style>
</head>
<body>

{title_html}
<div class="header">
  <div class="header-title">AutoResearch</div>
  <div class="header-goal">{goal or 'No research initialized'}</div>
</div>

<div class="stats">
  <div class="stat">
    <div class="stat-value">{total}</div>
    <div class="stat-label">Experiments</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--green)">{kept}</div>
    <div class="stat-label">Kept</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--red)">{reverted}</div>
    <div class="stat-label">Reverted</div>
  </div>
  <div class="stat">
    <div class="stat-value" style="color:var(--blue)">{f'{best_val}' if best_val is not None else '—'}</div>
    <div class="stat-label">Best Metric</div>
  </div>
</div>

<div id="chart-section" class="chart-container" style="display:{'block' if metric_series else 'none'}">
  <div class="chart-title">Metric History</div>
  <canvas id="metricChart"></canvas>
</div>

<div class="log" id="log-section">
  <div class="log-title">Experiment Log</div>
  <div id="log-entries"></div>
</div>

<script>
(function() {{
  const attempts = {attempts_json};
  const series = {series_json};
  const baseline = {json.dumps(baseline)};

  if (attempts.length === 0) {{
    document.getElementById('log-section').innerHTML =
      '<div class="empty-state">No experiments yet<div class="empty-hint">Use /autoresearch to start the optimization loop</div></div>';
    return;
  }}

  const logEl = document.getElementById('log-entries');
  let html = '';
  attempts.slice().reverse().forEach((a, idx) => {{
    const num = attempts.length - idx;
    const outcome = a.outcome || 'unknown';
    const badgeClass = 'badge-' + outcome;
    const metric = (a.old_val != null && a.new_val != null)
      ? a.old_val + ' → ' + a.new_val
      : '';
    html += `<div class="log-entry">
      <span class="log-num">#${{num}}</span>
      <span class="log-badge ${{badgeClass}}">${{outcome}}</span>
      <span class="log-desc">${{a.description || ''}}</span>
      <span class="log-metric">${{metric}}</span>
    </div>`;
  }});
  logEl.innerHTML = html;

  if (series.length < 2) return;

  const ctx = document.getElementById('metricChart');
  const labels = series.map(s => '#' + s.i);
  const values = series.map(s => s.val);
  const colors = series.map(s =>
    s.outcome === 'kept' ? '{ACCENT_GREEN}' :
    s.outcome === 'reverted' ? '{ACCENT_RED}' : '{TEXT_DIM}'
  );

  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: labels,
      datasets: [
        {{
          label: 'Metric',
          data: values,
          borderColor: '{ACCENT_BLUE}',
          backgroundColor: 'rgba(110,115,255,0.1)',
          borderWidth: 2,
          pointBackgroundColor: colors,
          pointBorderColor: colors,
          pointRadius: 5,
          pointHoverRadius: 7,
          fill: true,
          tension: 0.2,
        }},
        ...(baseline !== null ? [{{
          label: 'Baseline',
          data: Array(labels.length).fill(baseline),
          borderColor: '{TEXT_DIM}',
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
          fill: false,
        }}] : []),
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{
        legend: {{
          labels: {{ color: '{TEXT_SECONDARY}', font: {{ family: "{FONT}", size: 10 }} }}
        }},
        tooltip: {{
          callbacks: {{
            afterLabel: function(ctx) {{
              if (ctx.datasetIndex === 0) {{
                const s = series[ctx.dataIndex];
                return s.outcome + (s.desc ? ': ' + s.desc : '');
              }}
            }}
          }}
        }}
      }},
      scales: {{
        x: {{ ticks: {{ color: '{TEXT_DIM}', font: {{ size: 10 }} }},
             grid: {{ color: '{BORDER}' }} }},
        y: {{ ticks: {{ color: '{TEXT_DIM}', font: {{ size: 10 }} }},
             grid: {{ color: '{BORDER}' }} }},
      }},
    }}
  }});
}})();
</script>
</body></html>'''

    out, effective_filename = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension='.html', output_dir=output_dir,
    )
    atomic_write_text(out / effective_filename, html)
    print(f'[display] Wrote autoresearch dashboard to {effective_filename}')
    return name or display_id
