"""PDF display addon — writes PDF files to the output directory and extracts content."""

from pathlib import Path
from ._base import atomic_copy, atomic_write_bytes, resolve_display_path


def show_pdf(path_or_bytes, filename='output.pdf', name=None, display_id=None):
    """Write a PDF file to the display output.

    Args:
        path_or_bytes: path to PDF file, or bytes
        filename: output filename for unnamed displays (default: output.pdf)
        name: if given, writes to `<name>.pdf` — appears as a named tab.
        display_id: alias for `name`.
    """
    out, effective = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension='.pdf', force_extension=True,
    )
    target = out / effective
    if isinstance(path_or_bytes, (str, Path)):
        atomic_copy(path_or_bytes, target)
    else:
        atomic_write_bytes(target, path_or_bytes)
    print(f'[display] Wrote {effective}')
    return name or display_id


def read_pdf(path, page=None):
    """Extract text from a PDF file.

    Args:
        path: path to PDF file
        page: specific page number (1-indexed), or None for all pages

    Returns:
        dict with text content and page info
    """
    import pdfplumber
    pdf = pdfplumber.open(path)
    if page is not None:
        p = pdf.pages[page - 1]
        result = {'text': p.extract_text() or '', 'page': page,
                  'totalPages': len(pdf.pages)}
    else:
        texts = [(p.extract_text() or '') for p in pdf.pages]
        result = {'text': '\n\n'.join(texts), 'totalPages': len(pdf.pages)}
    pdf.close()
    return result


def screenshot_pdf(path, page=1):
    """Render a PDF page as a PNG image and save to snapshots.

    Args:
        path: path to PDF file
        page: page number (1-indexed, default 1)

    Returns:
        path to the saved PNG
    """
    import pdfplumber
    snapshot_path = Path(path).parent.parent / 'snapshots' / 'latest.png'
    pdf = pdfplumber.open(path)
    p = pdf.pages[page - 1]
    img = p.to_image(resolution=150)
    img.save(str(snapshot_path))
    pdf.close()
    print(f'[pdf] Rendered page {page} to {snapshot_path}')
    return str(snapshot_path)
