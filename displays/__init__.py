"""Triptych display-side addons — one renderer per file."""

from .matplotlib import show_figure
from .plotly import show_plotly
from .latex import show_latex
from .html import show_html
from .image import show_image
from .pdf import show_pdf, read_pdf, screenshot_pdf
from .markdown import show_markdown
from .code import show_code, show_diff
from .table import show_table, show_dataframe
from .d3 import show_d3, d3_scaffold
from .threejs import show_threejs, show_surface, show_vector_field, show_parametric, show_scene_preview
from .research import show_research
from .progress import show_progress
from .assumptions import show_assumptions
from .claims_status import show_claims_status
from .questions import show_questions, read_answers, wait_for_answers
from .derivation import show_derivation
from .autoresearch import show_autoresearch
from .circuitjs import show_circuitjs_waveform, show_circuitjs_bode, show_circuit_schematic
from .watch import show_watch
from ._base import (
    clear, clear_display, cleanup_displays,
    focus_display, active_display,
    OUTPUT_DIR,
)
from ._page import render_page, write_page
from ._command import query_workspace
