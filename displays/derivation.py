"""Derivation display — step-by-step mathematical derivations with KaTeX."""

import html as html_mod
from ._base import (BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_BLUE,
                    BORDER)
from ._page import write_page

DERIVATION_HEAD = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">'
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>'
    f'<style>'
    f'.tp-body{{max-width:800px;margin:0 auto;font-size:14px;line-height:1.6;'
    f'padding:12px 40px 32px;}}'
    f'.deriv-step{{background:{BG_SURFACE};border:1px solid {BORDER};'
    f'border-radius:8px;padding:20px 24px;margin-bottom:16px;}}'
    f'.deriv-num{{font-size:11px;color:{ACCENT_BLUE};text-transform:uppercase;'
    f'letter-spacing:0.08em;font-weight:600;margin-bottom:12px;}}'
    f'.deriv-math{{text-align:center;margin:8px 0 14px;font-size:20px;color:{TEXT_PRIMARY};}}'
    f'.deriv-explain{{font-size:13px;color:{TEXT_SECONDARY};line-height:1.5;}}'
    f'.katex{{font-size:1.3em;}}'
    f'.katex-html .highlight{{background:rgba(110,115,255,0.15);'
    f'border-radius:3px;padding:0 2px;}}'
    f'</style>'
)


def show_derivation(steps, title="Derivation", highlight=False,
                    filename='index.html', name=None, display_id=None):
    """Show a step-by-step mathematical derivation.

    Args:
        steps: list of tuples (latex_equation, explanation_text)
        title: optional title for the derivation
        highlight: if True, highlight differences between consecutive steps
                   (reserved — currently styling-only)
        filename: output filename for unnamed displays
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    _ = highlight  # reserved for future per-step diff highlighting
    blocks = []
    for i, (latex, explanation) in enumerate(steps, 1):
        blocks.append(
            '<div class="deriv-step">'
            f'<div class="deriv-num">Step {i}</div>'
            f'<div class="deriv-math" data-tex="{html_mod.escape(latex)}"></div>'
            f'<div class="deriv-explain">{html_mod.escape(explanation)}</div>'
            '</div>'
        )

    body = ''.join(blocks) + (
        '<script>'
        'document.querySelectorAll(".deriv-math").forEach(function(el){'
        'katex.render(el.getAttribute("data-tex"),el,'
        '{displayMode:true,throwOnError:false});});'
        '</script>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=DERIVATION_HEAD,
    )
