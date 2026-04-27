"""Markdown display — renders markdown as dark-themed HTML with math support."""

import json
from ._base import BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, ACCENT
from ._page import write_page

MD_HEAD = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">'
    '<script src="https://cdn.jsdelivr.net/npm/markdown-it@14/dist/markdown-it.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/markdown-it-texmath@1/texmath.min.js"></script>'
    f'<style>'
    f'.tp-body{{max-width:800px;margin:0 auto;font-size:14px;line-height:1.6;}}'
    f'h1{{font-size:28px;font-weight:500;color:#e0d8d0;margin:24px 0 12px;}}'
    f'h2{{font-size:22px;font-weight:500;color:#d8d0c8;margin:20px 0 10px;}}'
    f'h3{{font-size:18px;font-weight:500;color:#c8c0b8;margin:16px 0 8px;}}'
    f'p{{margin:8px 0;}} strong{{color:#e0d8d0;}}'
    f'code{{background:#282320;padding:2px 5px;border-radius:3px;'
    f'font-size:0.9em;color:{ACCENT};}}'
    f'pre{{background:{BG_SURFACE};border:1px solid {BORDER};'
    f'border-radius:6px;padding:12px 16px;margin:12px 0;overflow-x:auto;}}'
    f'pre code{{background:transparent;padding:0;color:{TEXT_PRIMARY};}}'
    f'blockquote{{border-left:3px solid {ACCENT};padding-left:16px;'
    f'margin:12px 0;color:{TEXT_SECONDARY};}}'
    f'ul,ol{{padding-left:24px;margin:8px 0;}} li{{margin:4px 0;}}'
    f'a{{color:{ACCENT};}} hr{{border:none;border-top:1px solid {BORDER};margin:20px 0;}}'
    f'table{{border-collapse:collapse;margin:12px 0;width:100%;}}'
    f'th,td{{border:1px solid {BORDER};padding:6px 10px;text-align:left;}}'
    f'th{{background:{BG_SURFACE};color:{TEXT_SECONDARY};font-weight:500;font-size:11px;}}'
    f'.katex{{font-size:1.1em;}} .katex-display{{margin:16px 0;}}'
    f'</style>'
)


def show_markdown(md_string, filename='index.html', title=None,
                  name=None, display_id=None):
    """Render markdown as an HTML page with dark theme and KaTeX math.

    Uses markdown-it + KaTeX from CDN for client-side rendering.

    Args:
        md_string: Markdown string
        filename: output filename for unnamed displays
        title: optional title shown above content
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    body = (
        '<div id="content"></div>'
        f'<script>window.addEventListener("load",function(){{'
        'var md=window.markdownit({html:true,linkify:true,typographer:true});'
        'if(window.texmath&&window.katex){'
        'md.use(window.texmath,{engine:katex,delimiters:"dollars"});}'
        f'document.getElementById("content").innerHTML=md.render({json.dumps(md_string)});'
        '}});</script>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=MD_HEAD,
    )
