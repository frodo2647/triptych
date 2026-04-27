"""Matplotlib renderer — saves figures as dark-themed HTML with embedded PNG."""

import io
import base64
from ._base import BG_VOID
from ._page import write_page

MPL_HEAD = (
    '<style>'
    '.tp-body{display:flex;flex-direction:column;align-items:center;'
    'justify-content:center;flex:1;padding:16px;height:calc(100vh - 0px);}'
    '.tp-figure-wrap{width:100%;display:flex;align-items:center;'
    'justify-content:center;flex:1;}'
    '.tp-figure-wrap img{max-width:100%;max-height:100%;width:auto;height:auto;'
    'border-radius:4px;object-fit:contain;}'
    '</style>'
)


def show_figure(fig, filename='index.html', title=None,
                name=None, display_id=None):
    """Save a matplotlib figure as an embedded HTML page with dark theme.

    Args:
        fig: matplotlib Figure object
        filename: output filename for unnamed displays
        title: optional title shown above the figure
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                facecolor=BG_VOID, edgecolor='none', transparent=False)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    body = (
        '<div class="tp-figure-wrap">'
        f'<img src="data:image/png;base64,{img_b64}" alt="Figure">'
        '</div>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=MPL_HEAD,
    )
