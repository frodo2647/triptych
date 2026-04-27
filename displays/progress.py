"""Progress display — live dashboard for multi-step work.

`show_progress` is the collaboration primitive: during long-running tasks
(training runs, staged plans, long derivations, research sweeps), keep this
display up and updated so the human can steer without reading scrollback.

Each call merges new inputs into persistent state at
`workspace/research/progress-<name>/progress.json`:

  - `steps`   → replaces the step list (source-of-truth each call)
  - `metrics` → appended to metrics_history with a timestamp
  - `decisions` → extended (append-only log)
  - `goal`    → set if provided

Status values for steps: pending | active | done | failed
"""

import json
import time
import html as html_mod
from pathlib import Path

from core.paths import RESEARCH_DIR as PROGRESS_ROOT
from ._base import (OUTPUT_DIR, BG_VOID, BG_SURFACE, TEXT_PRIMARY,
                     TEXT_SECONDARY, TEXT_DIM, BORDER, FONT,
                     ACCENT, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
                     ACCENT_YELLOW, atomic_write_text, resolve_display_path)

STATUS_COLORS = {
    'pending': TEXT_DIM,
    'active': ACCENT_YELLOW,
    'done': ACCENT_GREEN,
    'failed': ACCENT_RED,
}


def _state_path(name):
    d = PROGRESS_ROOT / f'progress-{name}'
    d.mkdir(parents=True, exist_ok=True)
    return d / 'progress.json'


def _load_state(name):
    p = _state_path(name)
    if not p.exists():
        return {
            'name': name,
            'goal': '',
            'steps': [],
            'metrics_history': [],
            'decisions': [],
            'created': time.time(),
        }
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return {'name': name, 'goal': '', 'steps': [],
                'metrics_history': [], 'decisions': [], 'created': time.time()}


def _save_state(name, state):
    p = _state_path(name)
    atomic_write_text(p, json.dumps(state, indent=2))


def show_progress(steps=None, metrics=None, decisions=None, goal=None,
                  name='progress', display_id=None,
                  output_dir=None, filename='index.html'):
    """Render a live progress dashboard and persist state.

    Parameters
    ----------
    steps : list of dict, optional
        Each step: {"name": str, "status": "pending"|"active"|"done"|"failed",
                    "note": str (optional)}. Replaces the current step list.
    metrics : dict, optional
        Numeric metrics to append to history, e.g. {"loss": 0.12, "acc": 0.96}.
    decisions : list of str, optional
        Design decisions to append to the decisions log.
    goal : str, optional
        One-line description of what the work is trying to accomplish.
    name : str
        Namespace for this progress session. Multiple concurrent progress
        displays can coexist under different names.
    display_id : str, optional
        Forward-compat for the display pool (Phase 3). Currently ignored;
        the return value is usable as a pool id once Phase 3 lands.
    output_dir, filename : optional overrides for the HTML output location.

    Returns
    -------
    str
        The display id (currently the `name`). Pass this back as
        `display_id` on subsequent calls once the pool API exists.
    """
    state = _load_state(name)

    if goal is not None:
        state['goal'] = goal
    if steps is not None:
        state['steps'] = list(steps)
    if metrics is not None and isinstance(metrics, dict):
        entry = {'ts': time.time()}
        entry.update({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
        entry.update({k: v for k, v in metrics.items()
                      if not isinstance(v, (int, float))})
        state['metrics_history'].append(entry)
    if decisions is not None:
        ts = time.time()
        for d in decisions:
            state['decisions'].append({'ts': ts, 'text': str(d)})

    _save_state(name, state)

    html = _render(state)

    # Named progress displays become named tabs in the display pool.
    # The default name is 'progress', so even unnamed calls get a stable tab.
    out, effective_filename = resolve_display_path(
        name=name, default_filename=filename, extension='.html',
        output_dir=output_dir,
    )
    atomic_write_text(out / effective_filename, html)
    print(f'[display] Wrote progress dashboard ({name}) to {effective_filename}')

    return name


def _render(state):
    steps = state.get('steps', [])
    metrics_history = state.get('metrics_history', [])
    decisions = state.get('decisions', [])
    goal = state.get('goal', '') or 'No goal set'
    name = state.get('name', 'progress')

    total = len(steps)
    done = sum(1 for s in steps if s.get('status') == 'done')
    active = sum(1 for s in steps if s.get('status') == 'active')
    failed = sum(1 for s in steps if s.get('status') == 'failed')
    pct = int(round(100 * done / total)) if total else 0

    latest = metrics_history[-1] if metrics_history else {}
    metric_keys = [k for k in latest.keys() if k != 'ts']

    series = {k: [] for k in metric_keys}
    for entry in metrics_history:
        for k in metric_keys:
            v = entry.get(k)
            if isinstance(v, (int, float)):
                series[k].append(v)

    state_json = json.dumps({
        'steps': steps,
        'metrics_history': metrics_history,
        'decisions': decisions,
        'series': series,
        'metric_keys': metric_keys,
    })

    safe_goal = html_mod.escape(goal)
    safe_name = html_mod.escape(name)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  :root {{
    --void: {BG_VOID}; --surface: {BG_SURFACE};
    --text: {TEXT_PRIMARY}; --text-2: {TEXT_SECONDARY}; --text-3: {TEXT_DIM};
    --border: {BORDER}; --accent: {ACCENT};
    --blue: {ACCENT_BLUE}; --green: {ACCENT_GREEN};
    --red: {ACCENT_RED}; --yellow: {ACCENT_YELLOW};
    --font: {FONT};
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{ background: var(--void); color: var(--text);
                font-family: var(--font); font-size: 13px; line-height: 1.55; }}
  html {{ scrollbar-color: var(--border) transparent; }}

  /* ── Header ─────────────────────────────────────── */
  .header {{
    background: var(--surface); border-bottom: 1px solid var(--border);
    padding: 18px 28px; display: flex; align-items: flex-start;
    justify-content: space-between; gap: 24px;
  }}
  .header-left {{ flex: 1; min-width: 0; }}
  .header-kicker {{
    font-size: 10px; color: var(--text-3); letter-spacing: 0.12em;
    text-transform: uppercase; margin-bottom: 4px;
  }}
  .header-goal {{ font-size: 15px; color: var(--text); font-weight: 500; }}
  .header-name {{ font-size: 11px; color: var(--text-3); margin-top: 3px; }}

  .progress-pill {{
    flex-shrink: 0; text-align: right;
  }}
  .progress-count {{ font-size: 20px; color: var(--text); font-weight: 600; }}
  .progress-count em {{ color: var(--text-3); font-style: normal; font-weight: 400; }}
  .progress-pct {{ font-size: 10px; color: var(--text-3);
                   letter-spacing: 0.08em; text-transform: uppercase; }}

  .progress-bar {{
    height: 3px; background: var(--border); margin-top: 12px;
    border-radius: 2px; overflow: hidden;
  }}
  .progress-bar-fill {{
    height: 100%; background: var(--green);
    width: {pct}%; transition: width 0.3s;
  }}

  /* ── Sections ────────────────────────────────────── */
  .section {{
    padding: 20px 28px; border-bottom: 1px solid var(--border);
  }}
  .section:last-child {{ border-bottom: none; }}
  .section-title {{
    font-size: 10px; font-weight: 600; color: var(--text-2);
    letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 12px;
  }}

  /* ── Steps ───────────────────────────────────────── */
  .steps {{ display: flex; flex-direction: column; gap: 4px; }}
  .step {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 6px 10px; border-radius: 4px;
    font-size: 13px;
    background: transparent;
    transition: background 0.15s;
  }}
  .step.active {{ background: rgba(196,160,69,0.08); }}
  .step-chip {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; padding: 2px 7px; border-radius: 3px;
    flex-shrink: 0; min-width: 60px; text-align: center; margin-top: 2px;
  }}
  .chip-pending {{ background: rgba(104,95,86,0.16); color: var(--text-3); }}
  .chip-active  {{ background: rgba(196,160,69,0.16); color: var(--yellow); }}
  .chip-done    {{ background: rgba(60,196,151,0.16); color: var(--green); }}
  .chip-failed  {{ background: rgba(212,117,103,0.16); color: var(--red); }}
  .step-body {{ flex: 1; min-width: 0; }}
  .step-name {{ color: var(--text); }}
  .step.pending .step-name {{ color: var(--text-3); }}
  .step.done .step-name {{ color: var(--text-2); text-decoration: line-through;
                            text-decoration-color: var(--border); }}
  .step-note {{ font-size: 11px; color: var(--text-3); margin-top: 2px; }}

  .empty {{ color: var(--text-3); font-size: 12px; padding: 8px 0; }}

  /* ── Metrics ─────────────────────────────────────── */
  .metrics {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
  }}
  .metric {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 10px 12px;
  }}
  .metric-label {{
    font-size: 10px; color: var(--text-3);
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px;
  }}
  .metric-value {{
    font-size: 18px; color: var(--text); font-weight: 500;
    font-variant-numeric: tabular-nums;
  }}
  .metric-spark {{ margin-top: 6px; height: 22px; width: 100%; }}
  .metric-delta {{ font-size: 10px; color: var(--text-3); margin-top: 2px; }}
  .metric-delta.up {{ color: var(--green); }}
  .metric-delta.down {{ color: var(--red); }}

  /* ── Decisions ───────────────────────────────────── */
  .decisions {{ display: flex; flex-direction: column; gap: 8px; }}
  .decision {{
    display: flex; gap: 10px; font-size: 12px;
    padding: 8px 10px; background: var(--surface);
    border: 1px solid var(--border); border-left: 2px solid var(--accent);
    border-radius: 3px;
  }}
  .decision-marker {{
    color: var(--accent); font-weight: 600; flex-shrink: 0;
    font-size: 10px; padding-top: 1px;
  }}
  .decision-text {{ flex: 1; color: var(--text); }}
</style>
</head>
<body>

<header class="header">
  <div class="header-left">
    <div class="header-kicker">Progress</div>
    <div class="header-goal">{safe_goal}</div>
    <div class="header-name">{safe_name}</div>
  </div>
  <div class="progress-pill">
    <div class="progress-count">{done}<em>/{total}</em></div>
    <div class="progress-pct">{pct}% &middot; {active} active{(' &middot; ' + str(failed) + ' failed') if failed else ''}</div>
  </div>
</header>
<div class="progress-bar"><div class="progress-bar-fill"></div></div>

<section class="section">
  <div class="section-title">Steps</div>
  <div class="steps" id="steps"></div>
</section>

<section class="section" id="metrics-section">
  <div class="section-title">Metrics</div>
  <div class="metrics" id="metrics"></div>
</section>

<section class="section" id="decisions-section">
  <div class="section-title">Decisions</div>
  <div class="decisions" id="decisions"></div>
</section>

<script>
(function() {{
  const state = {state_json};
  const steps = state.steps || [];
  const metricsHistory = state.metrics_history || [];
  const decisions = state.decisions || [];
  const series = state.series || {{}};
  const metricKeys = state.metric_keys || [];

  // ── Steps ──
  const stepsEl = document.getElementById('steps');
  if (!steps.length) {{
    stepsEl.innerHTML = '<div class="empty">No steps yet.</div>';
  }} else {{
    let html = '';
    steps.forEach(s => {{
      const status = s.status || 'pending';
      const name = (s.name || '').toString();
      const note = (s.note || '').toString();
      html += '<div class="step ' + status + '">'
        + '<span class="step-chip chip-' + status + '">' + status + '</span>'
        + '<div class="step-body">'
        + '<div class="step-name">' + escapeHtml(name) + '</div>'
        + (note ? '<div class="step-note">' + escapeHtml(note) + '</div>' : '')
        + '</div></div>';
    }});
    stepsEl.innerHTML = html;
  }}

  // ── Metrics ──
  const metricsEl = document.getElementById('metrics');
  const metricsSection = document.getElementById('metrics-section');
  if (!metricsHistory.length || !metricKeys.length) {{
    metricsSection.style.display = 'none';
  }} else {{
    const latest = metricsHistory[metricsHistory.length - 1] || {{}};
    const prev = metricsHistory.length >= 2
      ? metricsHistory[metricsHistory.length - 2] : null;
    let html = '';
    metricKeys.forEach(k => {{
      const val = latest[k];
      if (val === undefined || val === null) return;
      const valueText = formatNum(val);
      const vals = series[k] || [];
      let deltaHtml = '';
      if (prev && typeof prev[k] === 'number' && typeof val === 'number') {{
        const d = val - prev[k];
        if (d !== 0) {{
          const cls = d > 0 ? 'up' : 'down';
          deltaHtml = '<div class="metric-delta ' + cls + '">'
            + (d > 0 ? '+' : '') + formatNum(d) + '</div>';
        }}
      }}
      html += '<div class="metric">'
        + '<div class="metric-label">' + escapeHtml(k) + '</div>'
        + '<div class="metric-value">' + valueText + '</div>'
        + (vals.length > 1
             ? '<svg class="metric-spark" data-series=\\'' + JSON.stringify(vals).replace(/'/g, "&#39;") + '\\'></svg>'
             : '')
        + deltaHtml
        + '</div>';
    }});
    metricsEl.innerHTML = html;
    document.querySelectorAll('.metric-spark').forEach(svg => {{
      try {{ drawSpark(svg, JSON.parse(svg.dataset.series)); }} catch(e) {{}}
    }});
  }}

  // ── Decisions ──
  const decEl = document.getElementById('decisions');
  const decSection = document.getElementById('decisions-section');
  if (!decisions.length) {{
    decSection.style.display = 'none';
  }} else {{
    let html = '';
    decisions.slice().reverse().forEach((d, idx) => {{
      const n = decisions.length - idx;
      const text = typeof d === 'string' ? d : (d.text || '');
      html += '<div class="decision">'
        + '<span class="decision-marker">#' + n + '</span>'
        + '<span class="decision-text">' + escapeHtml(text) + '</span>'
        + '</div>';
    }});
    decEl.innerHTML = html;
  }}

  // ── Helpers ──
  function escapeHtml(s) {{
    return String(s).replace(/[&<>"']/g, c =>
      ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
  }}
  function formatNum(v) {{
    if (typeof v !== 'number') return String(v);
    if (Number.isInteger(v)) return v.toString();
    const abs = Math.abs(v);
    if (abs >= 1000 || abs < 0.001) return v.toExponential(2);
    return v.toFixed(abs < 1 ? 4 : abs < 10 ? 3 : 2);
  }}
  function drawSpark(svg, vals) {{
    if (!vals || vals.length < 2) return;
    const w = svg.clientWidth || 160;
    const h = 22;
    const min = Math.min.apply(null, vals);
    const max = Math.max.apply(null, vals);
    const range = max - min || 1;
    const step = w / (vals.length - 1);
    let path = '';
    vals.forEach((v, i) => {{
      const x = i * step;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      path += (i === 0 ? 'M' : 'L') + x.toFixed(2) + ',' + y.toFixed(2);
    }});
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    svg.setAttribute('preserveAspectRatio', 'none');
    const last = vals[vals.length - 1];
    const lastX = (vals.length - 1) * step;
    const lastY = h - ((last - min) / range) * (h - 4) - 2;
    svg.innerHTML =
      '<path d="' + path + '" fill="none" stroke="{ACCENT_BLUE}" stroke-width="1.3"/>'
      + '<circle cx="' + lastX.toFixed(2) + '" cy="' + lastY.toFixed(2) + '" r="2" fill="{ACCENT}"/>';
  }}
}})();
</script>
</body></html>"""
