"""HTML renderer — writes raw HTML to the display."""

from ._base import atomic_write_text, resolve_display_path


def show_html(html_content, filename='index.html', name=None, display_id=None):
    """Write raw HTML to the display.

    Args:
        html_content: HTML string (must be a complete document — bypasses the
                      shared template).
        filename: output filename for unnamed displays (default: index.html)
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    out, effective = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension='.html',
    )
    atomic_write_text(out / effective, html_content)
    print(f'[display] Wrote {effective}')
    return name or display_id
