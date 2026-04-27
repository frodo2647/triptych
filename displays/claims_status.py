"""Claims-in-flight display — verification timeline for emitted claims.

`show_claims_status` reads `workspace/research/verification.log` and renders a
live timeline of claims and their verification verdicts. Pending claims pulse;
verified ones go green; failed ones go red; uncertain ones go yellow. The
human can see at a glance which claims are still in flight, which are
established, and which need attention.

Pair with `/loop 60s /verifier`. The verifier writes `result` entries to the
same log; calling `show_claims_status` again refreshes the display.

Reads from `core/verify.py`'s log shape:
  - {type: "claim", id: "C1", claim: "...", context: "...", depends: [...], timestamp}
  - {type: "result", claimId: "C1", status: "verified|failed|uncertain", method, detail, timestamp}
  - {type: "flag", kind, detail, timestamp}
"""

import html as html_mod
from pathlib import Path

from ._base import (OUTPUT_DIR, BG_VOID, BG_SURFACE, TEXT_PRIMARY,
                     TEXT_SECONDARY, TEXT_DIM, BORDER, FONT,
                     ACCENT, ACCENT_BLUE, ACCENT_GREEN, ACCENT_RED,
                     ACCENT_YELLOW, atomic_write_text, resolve_display_path)

STATUS_COLORS = {
    'pending': ACCENT_YELLOW,
    'verified': ACCENT_GREEN,
    'failed': ACCENT_RED,
    'uncertain': ACCENT,
}

STATUS_LABELS = {
    'pending': 'pending',
    'verified': 'verified',
    'failed': 'failed',
    'uncertain': 'uncertain',
}


def _build_claim_view(log):
    """Walk the log and produce one row per claim with current status + method."""
    claims = {}
    order = []
    for entry in log:
        if entry.get('type') == 'claim':
            cid = entry.get('id')
            if cid not in claims:
                order.append(cid)
            claims[cid] = {
                'id': cid,
                'claim': entry.get('claim', ''),
                'context': entry.get('context', ''),
                'depends': entry.get('depends', []) or [],
                'status': 'pending',
                'method': '',
                'detail': '',
                'claim_ts': entry.get('timestamp', 0),
                'result_ts': 0,
            }
    for entry in log:
        if entry.get('type') != 'result':
            continue
        cid = entry.get('claimId')
        if cid not in claims:
            continue
        status = entry.get('status', 'uncertain')
        if status not in STATUS_COLORS:
            status = 'uncertain'
        claims[cid]['status'] = status
        claims[cid]['method'] = entry.get('method', '')
        claims[cid]['detail'] = entry.get('detail', '')
        claims[cid]['result_ts'] = entry.get('timestamp', 0)
    return [claims[cid] for cid in order]


def _summary(rows):
    counts = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    return counts


def show_claims_status(*,
                       title='Claims in flight',
                       subtitle=None,
                       research_dir=None,
                       output_dir=None,
                       name='claims'):
    """Render the verification timeline to the display pool.

    Reads `verification.log`, groups by claim ID, and shows each claim with
    its current verdict. Re-call to refresh after the verifier writes new
    results.

    Parameters
    ----------
    title : str
        Header text.
    subtitle : str, optional
        One-line context (e.g. "for the Lagrangian derivation").
    research_dir : str or Path, optional
        Override default research directory.
    output_dir : str or Path, optional
        Override default ``workspace/output/``.
    name : str
        Display tab stem. Defaults to ``"claims"``.

    Returns
    -------
    str : path to the written HTML file.
    """
    try:
        from core.verify import read_log
    except ImportError:
        rows = []
    else:
        try:
            log = read_log(research_dir)
        except Exception:
            log = []
        rows = _build_claim_view(log)

    counts = _summary(rows)
    chips = ''
    for status in ('pending', 'verified', 'uncertain', 'failed'):
        if counts.get(status):
            color = STATUS_COLORS[status]
            chips += (
                f'<span class="chip">'
                f'<span class="chip-dot" style="background:{color}"></span>'
                f'<span class="chip-count">{counts[status]}</span>'
                f'<span class="chip-label">{STATUS_LABELS[status]}</span>'
                f'</span>'
            )

    if not rows:
        body_html = (
            '<div class="empty">'
            'No claims emitted yet. Use '
            '<code>core.verify.emit_claim(claim, context, depends)</code> '
            'to start the verification loop.'
            '</div>'
        )
    else:
        body_html = ''
        for r in rows:
            color = STATUS_COLORS[r['status']]
            label = STATUS_LABELS[r['status']]
            depends_html = ''
            if r['depends']:
                dep_chips = ''.join(
                    f'<span class="dep-chip">{html_mod.escape(str(d))}</span>'
                    for d in r['depends']
                )
                depends_html = f'<div class="depends">depends on {dep_chips}</div>'
            method_html = ''
            if r['method']:
                method_html = (
                    f'<span class="method">via {html_mod.escape(r["method"])}</span>'
                )
            detail_html = ''
            if r['detail']:
                detail_html = (
                    f'<div class="detail">{html_mod.escape(r["detail"])}</div>'
                )
            pulse_class = ' pulsing' if r['status'] == 'pending' else ''
            body_html += f'''
        <div class="claim" data-status="{r['status']}">
          <div class="row">
            <span class="status-dot{pulse_class}" style="background:{color}"></span>
            <div class="claim-col">
              <div class="claim-head">
                <span class="claim-id">{html_mod.escape(r['id'])}</span>
                <span class="claim-text">{html_mod.escape(r['claim'])}</span>
              </div>
              <div class="claim-context">{html_mod.escape(r['context'])}</div>
              {depends_html}
              {detail_html}
            </div>
            <div class="meta">
              {method_html}
              <span class="status-label" style="color:{color}">{label}</span>
            </div>
          </div>
        </div>'''

    subtitle_html = (
        f'<div class="subtitle">{html_mod.escape(subtitle)}</div>'
        if subtitle else ''
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
    line-height: 1.5;
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
  .claim {{
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 8px;
    background: var(--surface);
  }}
  .claim[data-status="failed"] {{ border-color: rgba(212, 117, 103, 0.3); }}
  .claim[data-status="verified"] {{ border-color: rgba(60, 196, 151, 0.2); }}
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
  .status-dot.pulsing {{
    animation: pulse 1.6s ease-in-out infinite;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(196, 160, 69, 0.5); }}
    50% {{ opacity: 0.6; box-shadow: 0 0 0 4px rgba(196, 160, 69, 0); }}
  }}
  .claim-col {{ flex: 1; min-width: 0; }}
  .claim-head {{
    display: flex;
    align-items: baseline;
    gap: 8px;
  }}
  .claim-id {{
    color: var(--text-3);
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    flex-shrink: 0;
  }}
  .claim-text {{ color: var(--text); }}
  .claim-context {{
    color: var(--text-3);
    font-size: 11px;
    margin-top: 2px;
  }}
  .depends {{
    color: var(--text-3);
    font-size: 10px;
    margin-top: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
  }}
  .dep-chip {{
    font-family: 'JetBrains Mono', monospace;
    padding: 1px 5px;
    background: rgba(255,255,255,0.03);
    border-radius: 3px;
  }}
  .detail {{
    color: var(--text-2);
    font-size: 11px;
    margin-top: 5px;
    padding-top: 5px;
    border-top: 1px solid var(--border);
  }}
  .meta {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    flex-shrink: 0;
  }}
  .method {{
    color: var(--text-3);
    font-size: 10px;
    font-style: italic;
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
    {body_html}
  </main>
</body></html>'''

    out, effective_filename = resolve_display_path(
        name=name, default_filename='claims.html', extension='.html',
        output_dir=output_dir,
    )
    target = out / effective_filename
    atomic_write_text(target, html)
    print(f'[display] Wrote {len(rows)} claim(s) to {effective_filename}')
    return str(target)
