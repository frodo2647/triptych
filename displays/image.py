"""Image renderer — writes image files to the display."""

from pathlib import Path
from ._base import atomic_copy, atomic_write_bytes, resolve_display_path


def show_image(image_path_or_bytes, filename='plot.png',
               name=None, display_id=None):
    """Write an image file to the display.

    Args:
        image_path_or_bytes: path to image file, or bytes
        filename: output filename for unnamed displays (default: plot.png)
        name: if given, writes to `<name>.<ext>` — appears as a named tab.
              Extension is inferred from the source filename when possible,
              otherwise defaults to `.png`.
        display_id: alias for `name`.
    """
    src_ext = None
    if isinstance(image_path_or_bytes, (str, Path)):
        src_ext = Path(image_path_or_bytes).suffix or None
    extension = src_ext or Path(filename).suffix or '.png'

    out, effective = resolve_display_path(
        name=name, display_id=display_id, default_filename=filename,
        extension=extension, force_extension=True,
    )
    target = out / effective
    if isinstance(image_path_or_bytes, (str, Path)):
        atomic_copy(image_path_or_bytes, target)
    else:
        atomic_write_bytes(target, image_path_or_bytes)
    print(f'[display] Wrote {effective}')
    return name or display_id
