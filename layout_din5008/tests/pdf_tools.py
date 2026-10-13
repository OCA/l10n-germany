# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Helpers extracting positions (mm from the top left corner) from a PDF page.

The content stream is walked directly so that the helpers work with every
pypdf implementation supported by Odoo (PyPDF2 1.26, PyPDF2 2.x and pypdf).
"""

import re

from odoo.tools.pdf import generic

try:
    ContentStream = generic.ContentStream
except AttributeError:  # PyPDF2 1.26
    from PyPDF2.pdf import ContentStream

MM_PER_PT = 25.4 / 72.0
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
_HEX = re.compile(rb"<([0-9A-Fa-f]*)>")
_TEXT_OPERATORS = (b"Tj", b"TJ", b"'", b'"')


def _call(obj, *names):
    """Call the first existing method of ``names`` (camelCase / snake_case)."""
    for name in names:
        method = getattr(obj, name, None)
        if method is not None:
            return method()
    raise AttributeError(names)


def _resolve(obj):
    return _call(obj, "get_object", "getObject") if hasattr(obj, "idnum") else obj


def _multiply(first, second):
    """Return the matrix product ``first x second`` (PDF 6 value matrices)."""
    a, b, c, d, e, f = first
    a2, b2, c2, d2, e2, f2 = second
    return (
        a * a2 + b * c2,
        a * b2 + b * d2,
        c * a2 + d * c2,
        c * b2 + d * d2,
        e * a2 + f * c2 + e2,
        e * b2 + f * d2 + f2,
    )


def _utf16(hex_value):
    return bytes.fromhex(hex_value.decode()).decode("utf-16-be", "replace")


def _parse_cmap(data):
    """Return a ``{glyph code: text}`` mapping from a ToUnicode CMap."""
    mapping = {}
    for block in re.finditer(rb"beginbfchar(.*?)endbfchar", data, re.S):
        tokens = _HEX.findall(block.group(1))
        for src, dst in zip(tokens[0::2], tokens[1::2], strict=True):
            mapping[int(src, 16)] = _utf16(dst)
    for block in re.finditer(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for line in block.group(1).splitlines():
            tokens = _HEX.findall(line)
            if len(tokens) < 3:
                continue
            low, high = int(tokens[0], 16), int(tokens[1], 16)
            if b"[" in line:
                for offset, dst in enumerate(tokens[2:]):
                    mapping[low + offset] = _utf16(dst)
            else:
                base = int(tokens[2], 16)
                for code in range(low, high + 1):
                    mapping[code] = chr(base + code - low)
    return mapping


def _font_maps(page):
    """Return ``{font resource name: glyph mapping or None}``."""
    maps = {}
    resources = _resolve(page.get("/Resources") or {})
    for name, font in _resolve(resources.get("/Font") or {}).items():
        font = _resolve(font)
        to_unicode = font.get("/ToUnicode")
        if to_unicode is None:
            maps[name] = None
            continue
        maps[name] = _parse_cmap(_call(_resolve(to_unicode), "get_data", "getData"))
    return maps


def _decode(raw, mapping):
    if isinstance(raw, str):
        # pypdf returns decodable strings as TextStringObject
        if hasattr(raw, "get_original_bytes"):
            raw = raw.get_original_bytes()
        else:
            raw = getattr(raw, "original_bytes", None) or raw.encode("latin-1")
    if mapping is None:
        return bytes(raw).decode("latin-1", "replace")
    codes = [int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw) - 1, 2)]
    return "".join(mapping.get(code, "") for code in codes)


def _page_height(page):
    box = getattr(page, "mediabox", None)
    if box is None:
        box = page.mediaBox
    return float(box[3]) - float(box[1])


def extract_positions(page):
    """Return ``(texts, rects)`` of a pypdf page.

    ``texts`` is a list of ``(text, x_mm, top_mm)`` where ``x`` is the start of
    the text run and ``top`` its baseline measured from the top edge.
    ``rects`` is a list of ``(x_mm, top_mm, width_mm, height_mm)`` of the
    rectangles drawn on the page (backgrounds, marks).
    """
    height = _page_height(page)
    fonts = _font_maps(page)
    content = ContentStream(_call(page, "get_contents", "getContents"), page.pdf)
    texts = []
    rects = []
    cm = IDENTITY
    stack = []
    tm = IDENTITY
    mapping = None
    run_text = ""
    run_start = None

    def to_mm(x, y):
        return x * MM_PER_PT, (height - y) * MM_PER_PT

    for operands, operator in content.operations:
        if operator == b"q":
            stack.append(cm)
        elif operator == b"Q":
            cm = stack.pop() if stack else IDENTITY
        elif operator == b"cm":
            cm = _multiply(tuple(float(value) for value in operands), cm)
        elif operator == b"re":
            x, y, width, rect_height = (float(value) for value in operands)
            x0, y0 = _multiply((1, 0, 0, 1, x, y), cm)[4:]
            x1, y1 = _multiply((1, 0, 0, 1, x + width, y + rect_height), cm)[4:]
            left, top = to_mm(min(x0, x1), max(y0, y1))
            rects.append(
                (left, top, abs(x1 - x0) * MM_PER_PT, abs(y1 - y0) * MM_PER_PT)
            )
        elif operator == b"BT":
            tm = IDENTITY
            run_text, run_start = "", None
        elif operator == b"Tf":
            mapping = fonts.get(str(operands[0]))
        elif operator == b"Tm":
            tm = tuple(float(value) for value in operands)
        elif operator in (b"Td", b"TD"):
            tx, ty = (float(value) for value in operands)
            tm = _multiply((1, 0, 0, 1, tx, ty), tm)
        elif operator in _TEXT_OPERATORS:
            if run_start is None:
                x, y = _multiply(tm, cm)[4:]
                run_start = to_mm(x, y)
            raw = operands[-1]
            parts = raw if isinstance(raw, list) else [raw]
            run_text += "".join(
                _decode(part, mapping)
                for part in parts
                if isinstance(part, (bytes, str))
            )
        elif operator == b"ET":
            if run_text.strip() and run_start is not None:
                texts.append((run_text.strip(), run_start[0], run_start[1]))
            run_text, run_start = "", None
    return texts, rects


def find_text(texts, prefix):
    """Return ``(x, top)`` of the first text run starting with ``prefix``."""
    for text, x, top in texts:
        if text.startswith(prefix):
            return x, top
    raise AssertionError(
        f"Text {prefix!r} not found in {[text for text, _, _ in texts]}"
    )


def find_marks(rects):
    """Return the DIN 5008 marks: thin filled rectangles at the left edge."""
    return sorted(
        (top, width)
        for x, top, width, height in rects
        if x < 0.5 and height < 1.0 and 3.0 < width < 10.0
    )
