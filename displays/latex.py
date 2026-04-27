"""LaTeX renderer — renders math using KaTeX CDN."""

import json
from ._page import write_page

KATEX_HEAD = (
    '<link rel="stylesheet" '
    'href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">'
    '<script defer '
    'src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>'
)


def show_latex(tex, filename='index.html', title=None, name=None, display_id=None):
    """Render LaTeX math as an HTML page using KaTeX CDN.

    Args:
        tex: LaTeX string (without $$ delimiters)
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    body = (
        '<div id="math" style="font-size:20px;text-align:center;'
        'padding:24px 0;"></div>'
        f'<script>window.addEventListener("load",function(){{'
        f'katex.render({json.dumps(tex)},document.getElementById("math"),'
        f'{{displayMode:true,throwOnError:false}});}});</script>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=KATEX_HEAD,
    )
