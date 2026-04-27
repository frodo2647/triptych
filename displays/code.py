"""Code display addon — syntax-highlighted code blocks with dark theme."""

import html as html_mod
from ._base import BG_SURFACE, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, FONT
from ._page import write_page

PRISM_HEAD = (
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/themes/prism-tomorrow.min.css">'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/prism.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/line-numbers/prism-line-numbers.min.js"></script>'
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1/plugins/line-numbers/prism-line-numbers.min.css">'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-python.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-javascript.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-typescript.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-json.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-yaml.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-bash.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-sql.min.js"></script>'
    '<script src="https://cdn.jsdelivr.net/npm/prismjs@1/components/prism-latex.min.js"></script>'
    f'<style>'
    f'pre[class*="language-"]{{background:{BG_SURFACE} !important;'
    f'border:1px solid {BORDER};border-radius:6px;'
    f'padding:16px !important;font-size:13px;font-family:{FONT};}}'
    f'code[class*="language-"]{{font-family:{FONT};font-size:13px;}}'
    f'.line-numbers .line-numbers-rows{{border-right-color:{BORDER} !important;}}'
    f'.line-numbers-rows > span::before{{color:#444 !important;}}'
    f'</style>'
)


def show_code(code, language='python', filename='index.html', title=None,
              name=None, display_id=None):
    """Display syntax-highlighted code using Prism.js.

    Args:
        code: Code string
        language: Language for syntax highlighting (default: python)
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    safe_code = html_mod.escape(code)
    safe_lang = html_mod.escape(language)
    body = (
        f'<pre class="line-numbers"><code class="language-{safe_lang}">'
        f'{safe_code}</code></pre>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=PRISM_HEAD,
    )


DIFF_HEAD = (
    f'<style>'
    f'.diff-container{{display:flex;gap:8px;}}'
    f'.diff-pane{{flex:1;}}'
    f'.diff-pane pre[class*="language-"]{{background:{BG_SURFACE} !important;'
    f'border:1px solid {BORDER};border-radius:6px;margin:0;'
    f'padding:12px !important;overflow-x:auto;'
    f'font-family:{FONT};font-size:12px;line-height:1.5;color:{TEXT_PRIMARY};}}'
    f'.diff-label{{font-size:10px;color:{TEXT_SECONDARY};margin-bottom:6px;'
    f'text-transform:uppercase;letter-spacing:0.05em;}}'
    f'.pane-old pre[class*="language-"]{{border-color:rgba(248,113,113,0.3);}}'
    f'.pane-new pre[class*="language-"]{{border-color:rgba(52,211,153,0.3);}}'
    f'</style>'
)


def show_diff(old, new, language='python', filename='index.html', title=None,
              name=None, display_id=None):
    """Display a side-by-side diff of two code strings.

    Args:
        old: Original code string
        new: Modified code string
        language: Language for syntax highlighting (e.g. 'python', 'javascript')
        filename: output filename for unnamed displays
        title: optional title
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    safe_old = html_mod.escape(old)
    safe_new = html_mod.escape(new)
    safe_lang = html_mod.escape(language)
    body = (
        '<div class="diff-container">'
        '<div class="diff-pane pane-old"><div class="diff-label">Before</div>'
        f'<pre><code class="language-{safe_lang}">{safe_old}</code></pre></div>'
        '<div class="diff-pane pane-new"><div class="diff-label">After</div>'
        f'<pre><code class="language-{safe_lang}">{safe_new}</code></pre></div>'
        '</div>'
    )
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=PRISM_HEAD + DIFF_HEAD,
    )
