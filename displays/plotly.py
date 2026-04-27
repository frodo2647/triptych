"""Plotly renderer — saves interactive charts as dark-themed HTML."""

from ._base import (BG_VOID, BG_SURFACE, TEXT_PRIMARY, FONT,
                    atomic_write_text, resolve_display_path)


def show_plotly(fig, filename='index.html', *, title=None,
                name=None, display_id=None):
    """Save a Plotly figure as an interactive HTML page with dark theme.

    Args:
        fig: plotly Figure object
        filename: output filename for unnamed displays
        title: optional figure title (set as Plotly layout title)
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    layout = dict(
        template='plotly_dark',
        paper_bgcolor=BG_VOID,
        plot_bgcolor=BG_SURFACE,
        font=dict(family=FONT.replace("'", ""), color=TEXT_PRIMARY),
        margin=dict(l=40, r=20, t=40, b=40),
        autosize=True,
    )
    if title is not None:
        layout['title'] = title
    fig.update_layout(**layout)
    html = fig.to_html(
        include_plotlyjs='cdn',
        full_html=True,
        default_width='100%',
        default_height='100%',
        config={'displayModeBar': True, 'displaylogo': False, 'responsive': True},
    )
    html = html.replace(
        '<body>',
        f'<body style="background:{BG_VOID};margin:0;height:100vh;">'
    )
    html = html.replace(
        '<head>',
        '<head><style>html,body{height:100%;margin:0}'
        '.plotly-graph-div{width:100%!important;height:100%!important}</style>',
        1,
    )
    out, effective = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension='.html',
    )
    atomic_write_text(out / effective, html)
    print(f'[display] Wrote {effective}')
    return name or display_id
