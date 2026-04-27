"""Questions display — flexible questionnaire that writes answers back to disk.

Use `show_questions(questions, name=...)` to render a form in the display panel.
The user fills it in and clicks Submit; answers are PUT to
`workspace/research/questions-<name>/answers.json`. Read them back with
`read_answers(name=...)` or block on `wait_for_answers(name=...)`.

Supported question types
========================

    single   : pick one option (chips)            — options=[...]
    multi    : pick any number (toggleable chips) — options=[...]
    text     : single-line text input             — placeholder='...'
    textarea : multi-line text input              — placeholder='...'
    number   : numeric input                      — min=, max=, step=
    slider   : numeric range with live readout    — min=, max=, step=, default=
    scale    : 1-N Likert chips with end labels   — min=1, max=5,
                                                     low_label='Disagree',
                                                     high_label='Agree'
    yesno    : compact yes/no chips

Per-question optional fields:
    `id`, `label`, `hint`, `placeholder`, `load_bearing` (bool)

Question schema (flat):
    show_questions([
        {'id': 'budget', 'label': 'Budget?', 'type': 'single',
         'options': ['Hard ceiling', 'Anchor', 'Open']},
        {'id': 'noise',  'label': 'Acceptable noise (dBA)',
         'type': 'slider', 'min': 30, 'max': 80, 'step': 1, 'default': 45},
        {'id': 'notes',  'label': 'Notes', 'type': 'textarea'},
    ])

Or grouped (renders each group as a card):
    show_questions([
        {'group': 'Budget', 'questions': [...]},
        {'group': 'Users',  'questions': [...]},
    ])

The display panel pulls /core/theme.css automatically so chrome matches the
rest of Triptych.
"""

import html as html_mod
import json
import time

from core.paths import RESEARCH_DIR
from ._base import atomic_write_text, resolve_display_path


def _state_dir(name):
    d = RESEARCH_DIR / f'questions-{name}'
    d.mkdir(parents=True, exist_ok=True)
    return d


def _normalize(questions):
    """Return (groups, flat_questions). Groups is a list of (title, [q...])."""
    if not questions:
        return [], []
    if isinstance(questions[0], dict) and 'questions' in questions[0]:
        groups = [(g.get('group', ''), list(g['questions'])) for g in questions]
        flat = [q for _, qs in groups for q in qs]
        return groups, flat
    return [('', list(questions))], list(questions)


def show_questions(questions, name='questions', title=None, intro=None,
                   submit_label='Submit answers'):
    """Render a questionnaire and persist its schema.

    Returns the `name` (use as `name=` to `read_answers` / `wait_for_answers`).
    """
    groups, flat = _normalize(questions)

    state_dir = _state_dir(name)
    atomic_write_text(state_dir / 'schema.json',
                      json.dumps({'questions': flat, 'created': time.time()}, indent=2))

    answers_path = f'research/questions-{name}/answers.json'
    page = _render(groups, name=name, title=title, intro=intro,
                   submit_label=submit_label, answers_path=answers_path)

    out, filename = resolve_display_path(name=name, default_filename='questions.html',
                                          extension='.html')
    atomic_write_text(out / filename, page)
    print(f'[display] Wrote questionnaire ({name}) to {filename}')
    return name


def read_answers(name='questions'):
    """Read submitted answers as a dict, or None if not yet submitted."""
    p = _state_dir(name) / 'answers.json'
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def wait_for_answers(name='questions', timeout=None, poll=2.0):
    """Block until answers exist on disk, returning the dict (or None on timeout)."""
    deadline = time.time() + timeout if timeout is not None else None
    while True:
        ans = read_answers(name)
        if ans is not None:
            return ans
        if deadline is not None and time.time() >= deadline:
            return None
        time.sleep(poll)


# ───────────────────────────────────────────────────────────────────────
# Rendering
# ───────────────────────────────────────────────────────────────────────


def _esc(s):
    return html_mod.escape(str(s))


def _render(groups, name, title, intro, submit_label, answers_path):
    safe_title = _esc(title) if title else 'Questions'
    safe_intro = _esc(intro) if intro else ''

    # Number questions across all groups so Q1, Q2, ... line up like school-server example.
    counter = {'n': 0}
    body_html = []
    for gtitle, qs in groups:
        items = ''.join(_render_question(q, counter) for q in qs)
        gt = (f'<div class="group-title">{_esc(gtitle)}</div>'
              if gtitle else '')
        body_html.append(f'<section class="group">{gt}{items}</section>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
<link rel="stylesheet" href="/core/theme.css">
<style>
  *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    background: var(--void); color: var(--text-hi);
    font-family: var(--font-sans); font-size: var(--text-base);
    line-height: var(--leading-body); min-height: 100%;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto;
           padding: var(--space-6) var(--space-5) var(--space-8); }}

  h1 {{ font-family: var(--font-display); font-weight: 500;
        font-size: var(--text-2xl); letter-spacing: var(--tracking-tight);
        margin: 0 0 var(--space-2); color: var(--text-hi); }}
  .sub {{ color: var(--text-mid); font-size: var(--text-sm);
          margin-bottom: var(--space-6); max-width: 64ch; }}

  .group {{ border: 1px solid var(--hairline); border-radius: var(--r-lg);
            padding: var(--space-4) var(--space-5);
            margin-bottom: var(--space-4); background: var(--surface); }}
  .group-title {{ font-family: var(--font-display); font-weight: 500;
                  font-size: var(--text-lg); color: var(--accent);
                  margin: 0 0 var(--space-3);
                  letter-spacing: var(--tracking-tight); }}

  .q {{ margin-bottom: var(--space-4); }}
  .q:last-child {{ margin-bottom: 0; }}
  .q-head {{ display: flex; align-items: baseline; gap: var(--space-2);
             flex-wrap: wrap; }}
  .q-num {{ color: var(--text-dim); font-family: var(--font-mono);
            font-size: var(--text-xs); }}
  .q-label {{ color: var(--text-hi); font-weight: 500;
              font-size: var(--text-base); }}
  .q-load {{ display: inline-block; font-size: var(--text-2xs);
             text-transform: uppercase; letter-spacing: var(--tracking-wide);
             padding: 2px 8px; border-radius: var(--r-sm);
             background: var(--accent-soft); color: var(--accent);
             vertical-align: middle; }}
  .q-load.opt {{ background: transparent; color: var(--text-dim);
                 border: 1px solid var(--hairline-hi); }}
  .q-hint {{ color: var(--text-mid); font-size: var(--text-sm);
             margin: var(--space-1) 0 var(--space-3); max-width: 64ch; }}

  .opts {{ display: flex; flex-wrap: wrap; gap: var(--space-2);
           margin-top: var(--space-2); }}
  .opt-btn {{ background: var(--surface-2); border: 1px solid var(--hairline-hi);
              color: var(--text-hi);
              padding: 7px 14px; border-radius: var(--r-md);
              font-family: var(--font-sans); font-size: var(--text-sm);
              cursor: pointer; transition: all var(--t-fast) var(--ease); }}
  .opt-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
  .opt-btn.sel {{ background: var(--accent-soft); border-color: var(--accent);
                  color: var(--accent); }}
  .opt-btn:focus-visible {{ outline: none; box-shadow: var(--ring-focus); }}

  /* Yes / no */
  .yesno {{ display: flex; gap: var(--space-2); }}
  .yesno .opt-btn {{ min-width: 72px; text-align: center; }}

  /* Scale (Likert) */
  .scale {{ display: flex; align-items: center; gap: var(--space-3);
            flex-wrap: wrap; }}
  .scale-chips {{ display: flex; gap: 4px; }}
  .scale-chip {{ width: 36px; height: 36px;
                 display: inline-flex; align-items: center; justify-content: center;
                 border: 1px solid var(--hairline-hi); border-radius: 50%;
                 background: var(--surface-2); color: var(--text-hi);
                 font-family: var(--font-mono); font-size: var(--text-sm);
                 cursor: pointer; transition: all var(--t-fast) var(--ease); }}
  .scale-chip:hover {{ border-color: var(--accent); color: var(--accent); }}
  .scale-chip.sel {{ background: var(--accent); border-color: var(--accent);
                     color: var(--void); }}
  .scale-end {{ color: var(--text-dim); font-size: var(--text-xs);
                font-style: italic; }}

  /* Slider */
  .slider-row {{ display: flex; align-items: center; gap: var(--space-3);
                 margin-top: var(--space-2); }}
  .slider-row input[type=range] {{
    flex: 1; -webkit-appearance: none; appearance: none;
    height: 4px; border-radius: 2px;
    background: var(--surface-2); outline: none;
  }}
  .slider-row input[type=range]::-webkit-slider-thumb {{
    -webkit-appearance: none; appearance: none;
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--accent); border: 2px solid var(--void);
    cursor: pointer; box-shadow: var(--shadow-sm);
  }}
  .slider-row input[type=range]::-moz-range-thumb {{
    width: 18px; height: 18px; border-radius: 50%;
    background: var(--accent); border: 2px solid var(--void); cursor: pointer;
  }}
  .slider-readout {{ font-family: var(--font-mono); font-size: var(--text-sm);
                     color: var(--accent); min-width: 4ch; text-align: right; }}
  .slider-bounds {{ display: flex; justify-content: space-between;
                    color: var(--text-dim); font-size: var(--text-xs);
                    font-family: var(--font-mono); margin-top: 4px; }}

  /* Inputs */
  textarea, input[type=text], input[type=number] {{
    width: 100%; box-sizing: border-box;
    background: var(--surface-2); border: 1px solid var(--hairline-hi);
    color: var(--text-hi); border-radius: var(--r-md);
    padding: 9px 12px; font-family: var(--font-sans); font-size: var(--text-sm);
    margin-top: var(--space-2); resize: vertical;
    transition: border-color var(--t-fast) var(--ease);
  }}
  textarea {{ min-height: 64px; line-height: var(--leading-snug); }}
  textarea:focus, input:focus {{
    outline: none; border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-soft);
  }}
  input[type=number] {{ max-width: 200px; }}

  .actions {{ display: flex; align-items: center; gap: var(--space-3);
              margin-top: var(--space-5); flex-wrap: wrap; }}
  .btn {{ background: var(--accent); color: var(--void); border: none;
          padding: 11px 22px; border-radius: var(--r-md);
          font-family: var(--font-sans); font-weight: 600;
          font-size: var(--text-sm); cursor: pointer;
          transition: all var(--t-fast) var(--ease);
          box-shadow: var(--shadow-sm); }}
  .btn:hover {{ background: var(--accent-hover); }}
  .btn:active {{ transform: translateY(1px); }}
  .btn.ghost {{ background: transparent; color: var(--text-mid);
                border: 1px solid var(--hairline-hi); box-shadow: none; }}
  .btn.ghost:hover {{ color: var(--text-hi); border-color: var(--text-mid);
                      background: var(--surface-2); }}
  .status {{ font-size: var(--text-sm); color: var(--text-mid); }}
  .status.ok {{ color: var(--ok); }}
  .status.err {{ color: var(--err); }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{safe_title}</h1>
  {f'<div class="sub">{safe_intro}</div>' if safe_intro else ''}

  {''.join(body_html)}

  <div class="actions">
    <button class="btn" id="submitBtn">{_esc(submit_label)}</button>
    <button class="btn ghost" id="resetBtn">Reset</button>
    <span class="status" id="status"></span>
  </div>
</div>

<script>
(function() {{
  const ANSWERS_PATH = {json.dumps(answers_path)};
  const QUESTIONNAIRE_NAME = {json.dumps(name)};
  const state = {{}};

  // ── Chip groups (single, multi, scale, yesno) ────────────
  document.querySelectorAll('[data-group="chips"]').forEach(group => {{
    const qid = group.dataset.q;
    const multi = group.dataset.multi === '1';
    state[qid] = multi ? [] : null;
    group.querySelectorAll('[data-value]').forEach(btn => {{
      btn.addEventListener('click', () => {{
        if (multi) {{
          btn.classList.toggle('sel');
          state[qid] = [...group.querySelectorAll('.sel')].map(b => b.dataset.value);
        }} else {{
          group.querySelectorAll('.sel').forEach(b => b.classList.remove('sel'));
          btn.classList.add('sel');
          state[qid] = btn.dataset.value;
        }}
      }});
    }});
  }});

  // ── Sliders ──────────────────────────────────────────────
  document.querySelectorAll('input[type=range][data-q]').forEach(input => {{
    const qid = input.dataset.q;
    const readout = input.parentElement.querySelector('.slider-readout');
    const update = () => {{
      state[qid] = Number(input.value);
      if (readout) readout.textContent = input.value;
    }};
    input.addEventListener('input', update);
    update();  // seed default value
  }});

  // ── Number / text / textarea: read at submit time ────────

  function collect() {{
    const out = {{...state}};
    document.querySelectorAll('input[type=text][data-q], input[type=number][data-q], textarea[data-q]').forEach(el => {{
      const v = el.value;
      if (typeof v === 'string') {{
        const trimmed = v.trim();
        if (trimmed) {{
          out[el.dataset.q] = el.type === 'number' ? Number(trimmed) : trimmed;
        }}
      }}
    }});
    return out;
  }}

  function setStatus(text, kind) {{
    const status = document.getElementById('status');
    status.textContent = text;
    status.classList.remove('ok', 'err');
    if (kind) status.classList.add(kind);
  }}

  document.getElementById('submitBtn').addEventListener('click', async () => {{
    const payload = JSON.stringify({{
      name: QUESTIONNAIRE_NAME,
      submitted_at: Date.now() / 1000,
      answers: collect(),
    }}, null, 2);
    setStatus('Submitting...');
    try {{
      const url = `/api/files/${{ANSWERS_PATH.split('/').map(encodeURIComponent).join('/')}}`;
      // Use text/plain so express.json() does NOT intercept and re-encode the body.
      const res = await fetch(url, {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'text/plain' }},
        body: payload,
      }});
      if (!res.ok) throw new Error(res.status + ' ' + res.statusText);
      setStatus('Submitted — Claude can read your answers now.', 'ok');
    }} catch (e) {{
      setStatus('Submit failed: ' + e.message, 'err');
    }}
  }});

  document.getElementById('resetBtn').addEventListener('click', () => {{
    document.querySelectorAll('.sel').forEach(b => b.classList.remove('sel'));
    document.querySelectorAll('textarea, input[type=text], input[type=number]')
            .forEach(el => el.value = '');
    document.querySelectorAll('input[type=range][data-q]').forEach(el => {{
      el.value = el.dataset.default || el.min || '0';
      el.dispatchEvent(new Event('input'));
    }});
    Object.keys(state).forEach(k => {{
      state[k] = Array.isArray(state[k]) ? [] : null;
    }});
    setStatus('');
  }});
}})();
</script>
</body>
</html>"""


def _render_question(q, counter):
    counter['n'] += 1
    n = counter['n']
    qid = q.get('id') or f'q{n}'
    qtype = q.get('type', 'text')
    label = _esc(q.get('label', ''))
    hint = q.get('hint', '')
    hint_html = f'<div class="q-hint">{_esc(hint)}</div>' if hint else ''
    load = ('<span class="q-load">load-bearing</span>'
            if q.get('load_bearing') else '')

    head = (f'<div class="q-head">'
            f'<span class="q-num">Q{n}</span>'
            f'<span class="q-label">{label}</span>'
            f'{load}</div>')

    body = _render_body(qtype, q, qid)
    return f'<div class="q">{head}{hint_html}{body}</div>'


def _render_body(qtype, q, qid):
    qid_attr = _esc(qid)

    if qtype == 'single' or qtype == 'multi':
        opts = q.get('options', [])
        multi_attr = ' data-multi="1"' if qtype == 'multi' else ''
        chips = ''.join(
            f'<button class="opt-btn" data-value="{_esc(o)}" type="button">'
            f'{_esc(o)}</button>'
            for o in opts
        )
        return (f'<div class="opts" data-group="chips" data-q="{qid_attr}"{multi_attr}>'
                f'{chips}</div>')

    if qtype == 'yesno':
        return (f'<div class="opts yesno" data-group="chips" data-q="{qid_attr}">'
                f'<button class="opt-btn" data-value="yes" type="button">Yes</button>'
                f'<button class="opt-btn" data-value="no" type="button">No</button>'
                f'</div>')

    if qtype == 'scale':
        lo = int(q.get('min', 1))
        hi = int(q.get('max', 5))
        low_label = q.get('low_label', '')
        high_label = q.get('high_label', '')
        chips = ''.join(
            f'<button class="scale-chip" data-value="{i}" type="button">{i}</button>'
            for i in range(lo, hi + 1)
        )
        low = f'<span class="scale-end">{_esc(low_label)}</span>' if low_label else ''
        high = f'<span class="scale-end">{_esc(high_label)}</span>' if high_label else ''
        return (f'<div class="scale" data-group="chips" data-q="{qid_attr}">'
                f'{low}<div class="scale-chips">{chips}</div>{high}'
                f'</div>')

    if qtype == 'slider':
        mn = q.get('min', 0)
        mx = q.get('max', 100)
        step = q.get('step', 1)
        default = q.get('default', mn)
        return (f'<div class="slider-row">'
                f'<input type="range" data-q="{qid_attr}" '
                f'min="{mn}" max="{mx}" step="{step}" value="{default}" '
                f'data-default="{default}">'
                f'<span class="slider-readout">{default}</span>'
                f'</div>'
                f'<div class="slider-bounds"><span>{mn}</span><span>{mx}</span></div>')

    if qtype == 'number':
        mn_attr = f' min="{q["min"]}"' if 'min' in q else ''
        mx_attr = f' max="{q["max"]}"' if 'max' in q else ''
        step_attr = f' step="{q["step"]}"' if 'step' in q else ''
        placeholder = _esc(q.get('placeholder', ''))
        return (f'<input type="number" data-q="{qid_attr}" '
                f'placeholder="{placeholder}"{mn_attr}{mx_attr}{step_attr}>')

    if qtype == 'text':
        placeholder = _esc(q.get('placeholder', ''))
        return f'<input type="text" data-q="{qid_attr}" placeholder="{placeholder}">'

    # Default to textarea (catches 'textarea' and unknown types).
    placeholder = _esc(q.get('placeholder', ''))
    return f'<textarea data-q="{qid_attr}" placeholder="{placeholder}"></textarea>'
