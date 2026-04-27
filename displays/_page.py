"""Shared page template for Triptych display addons.

Every `show_*` that emits HTML funnels through `write_page` so the
display panel gets uniform tokens, title styling, and atomic writes.
Addons supply only the body and any extra `<head>` tags they need.
"""

import html as _h

from ._base import (
    BG_VOID, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, FONT,
    atomic_write_text, resolve_display_path,
)

PAGE_CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ height: 100%; background: {BG_VOID}; color: {TEXT_PRIMARY};
              font-family: {FONT}; font-size: 13px; line-height: 1.55; }}
html {{ scrollbar-color: {BORDER} transparent; }}
.tp-title {{ font-size: 12px; color: {TEXT_SECONDARY};
             letter-spacing: 0.05em; padding: 18px 24px 0; }}
.tp-body {{ padding: 20px 24px; }}
"""


def render_page(body, *, title=None, head='', body_attrs=''):
    """Wrap a body fragment in the standard Triptych dark-themed page."""
    title_html = (
        f'<div class="tp-title">{_h.escape(title)}</div>' if title else ''
    )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<link rel="stylesheet" href="/core/theme.css">'
        f'<style>{PAGE_CSS}</style>{head}</head>'
        f'<body {body_attrs}>{title_html}'
        f'<div class="tp-body">{body}</div>'
        '</body></html>'
    )


def write_page(body, *, name=None, display_id=None, filename='index.html',
               title=None, head='', body_attrs='', output_dir=None):
    """Render a body fragment and write it to the display panel.

    `name=` makes the display appear as a named tab in the display panel.
    Multiple named writes coexist as sibling tabs.
    """
    html = render_page(body, title=title, head=head, body_attrs=body_attrs)
    out, effective = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension='.html', output_dir=output_dir,
    )
    atomic_write_text(out / effective, html)
    print(f'[display] Wrote {effective}')
    return name or display_id
