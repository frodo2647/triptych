"""Table display addon — dark-themed HTML tables for data."""

import html as html_mod
from ._base import BG_SURFACE, TEXT_SECONDARY, BORDER
from ._page import write_page

TABLE_HEAD = (
    f'<style>'
    f'.tp-body{{font-size:12px;}}'
    f'.tp-table-info{{font-size:10px;color:{TEXT_SECONDARY};margin-bottom:8px;}}'
    f'table{{border-collapse:collapse;width:100%;}}'
    f'th{{background:{BG_SURFACE};color:{TEXT_SECONDARY};font-weight:500;'
    f'font-size:10px;text-transform:uppercase;letter-spacing:0.05em;'
    f'padding:6px 10px;border:1px solid {BORDER};text-align:left;'
    f'position:sticky;top:0;}}'
    f'td{{padding:5px 10px;border:1px solid {BORDER};}}'
    f'td.num{{text-align:right;font-variant-numeric:tabular-nums;}}'
    f'tr:hover td{{background:rgba(110,115,255,0.05);}}'
    f'</style>'
)


def show_table(data, columns=None, filename='index.html', title=None,
               name=None, display_id=None):
    """Display data as a dark-themed HTML table.

    Args:
        data: list of dicts, list of lists, or pandas DataFrame
        columns: column names (auto-detected from dicts/DataFrame)
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    rows, cols = _normalize(data, columns)

    header_cells = ''.join(
        f'<th>{html_mod.escape(str(c))}</th>' for c in cols
    ) if cols else ''
    header_row = f'<tr>{header_cells}</tr>' if cols else ''

    body_rows = []
    for row in rows:
        cells = ''.join(
            f'<td class="{"num" if _is_numeric(v) else ""}">'
            f'{html_mod.escape(str(v))}</td>'
            for v in row
        )
        body_rows.append(f'<tr>{cells}</tr>')

    n_cols = len(cols) if cols else (len(rows[0]) if rows else 0)
    body = (
        f'<div class="tp-table-info">{len(rows)} rows × {n_cols} columns</div>'
        f'<table><thead>{header_row}</thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=TABLE_HEAD,
    )


def show_dataframe(df, filename='index.html', title=None,
                   name=None, display_id=None):
    """Display a pandas DataFrame as a dark-themed table.

    Args:
        df: pandas DataFrame
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    info_title = title or f'DataFrame ({df.shape[0]} × {df.shape[1]})'
    return show_table(df, columns=list(df.columns), filename=filename,
                      title=info_title, name=name, display_id=display_id)


def _normalize(data, columns):
    """Normalize various input formats to (rows, columns)."""
    if hasattr(data, 'iterrows'):
        cols = columns or list(data.columns)
        rows = [list(row) for _, row in data.iterrows()]
        return rows, cols

    if not data:
        return [], columns or []

    if isinstance(data[0], dict):
        cols = columns or list(data[0].keys())
        rows = [[item.get(c, '') for c in cols] for item in data]
        return rows, cols

    rows = [list(row) for row in data]
    return rows, columns


def _is_numeric(val):
    """Check if a value looks numeric."""
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False
