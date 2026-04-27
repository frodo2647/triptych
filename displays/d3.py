"""D3 display addon — scaffolding for custom D3.js visualizations."""

import json
from ._base import TEXT_PRIMARY, TEXT_SECONDARY, BORDER, FONT
from ._page import write_page

D3_SCRIPT = '<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>'

D3_HEAD = (
    D3_SCRIPT
    + f'<style>'
    f'.tp-body{{display:flex;align-items:center;justify-content:center;'
    f'min-height:100vh;padding:20px;}}'
    f'svg{{overflow:visible;}}'
    f'text{{fill:{TEXT_PRIMARY};font-family:{FONT};font-size:11px;}}'
    f'.axis text{{fill:{TEXT_SECONDARY};font-size:10px;}}'
    f'.axis line,.axis path{{stroke:{BORDER};}}'
    f'.grid line{{stroke:{BORDER};stroke-opacity:0.5;}}'
    f'</style>'
)


def _d3_body(body_js, width, height, data):
    data_script = (
        f'const data = {json.dumps(data)};' if data is not None else ''
    )
    return (
        f'<svg id="viz" width="{width}" height="{height}"></svg>'
        '<script>'
        '(function(){'
        'const svg = d3.select("#viz");'
        f'const width = {width};'
        f'const height = {height};'
        'const margin = { top: 20, right: 20, bottom: 40, left: 50 };'
        'const innerWidth = width - margin.left - margin.right;'
        'const innerHeight = height - margin.top - margin.bottom;'
        'const g = svg.append("g")'
        '.attr("transform", `translate(${margin.left},${margin.top})`);'
        'const colors = ['
        f'"{TEXT_PRIMARY}","#cc7a58","#3cc497","#d47567","#c4a045","#7a80d5","{TEXT_SECONDARY}"'
        '];'
        f'{data_script}'
        f'{body_js}'
        '})();'
        '</script>'
    )


def d3_scaffold(body_js, width=800, height=600, data=None):
    """Generate complete HTML for a D3 visualization.

    Returns the rendered page string. Use `show_d3` to write directly.
    """
    from ._page import render_page
    return render_page(_d3_body(body_js, width, height, data), head=D3_HEAD)


def show_d3(js_code, data=None, width=800, height=600, filename='index.html',
            title=None, name=None, display_id=None):
    """Write a D3 visualization to the display.

    Args:
        js_code: JavaScript code using d3, svg, g, width, height,
                 innerWidth, innerHeight, colors, margin
        data: optional data embedded as JSON (accessible as `data` in JS)
        width: SVG width
        height: SVG height
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    body = _d3_body(js_code, width, height, data)
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=D3_HEAD,
    )
