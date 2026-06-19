"""HTML -> text normalization.

A small, original HTML stripper built on the standard library's
``html.parser``. It removes script/style/noscript content, drops tags,
decodes entities, and collapses whitespace so that two captures of the
same page produce identical text when only markup or whitespace differs.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

# Tags whose textual content is noise for change monitoring.
_SKIP_CONTENT_TAGS = {"script", "style", "noscript", "template", "head"}

# Block-level tags that should force a line break in the extracted text so
# that structurally distinct sections do not get glued together.
_BLOCK_TAGS = {
    "p", "div", "br", "li", "ul", "ol", "tr", "table", "section",
    "article", "header", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
    "blockquote", "pre", "hr", "nav", "main", "aside",
}


class _TextExtractor(HTMLParser):
    """Collect human-visible text from an HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in _SKIP_CONTENT_TAGS:
            self._skip_depth += 1
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_startendtag(self, tag: str, attrs) -> None:
        if tag.lower() in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _SKIP_CONTENT_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def html_to_text(html: str) -> str:
    """Extract visible text from an HTML string.

    Falls back gracefully on malformed markup (``HTMLParser`` is lenient).
    """
    extractor = _TextExtractor()
    extractor.feed(html)
    extractor.close()
    return normalize_text(extractor.get_text())


_WS_RUN = re.compile(r"[ \t\f\v]+")
_BLANK_LINES = re.compile(r"\n{2,}")


def normalize_text(text: str) -> str:
    """Collapse insignificant whitespace into a stable canonical form.

    - Normalizes all line endings to ``\\n``.
    - Trims trailing/leading whitespace on each line.
    - Collapses runs of spaces/tabs to a single space.
    - Removes blank lines and leading/trailing blank space.

    The goal is that markup reflow or whitespace churn does not register as
    a content change, while genuine wording changes do.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        line = _WS_RUN.sub(" ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)
