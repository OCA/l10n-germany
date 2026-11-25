# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

import lxml.html
from markupsafe import Markup, escape

from odoo import models
from odoo.tools import html2plaintext

# Letterhead height (= paper format margin top) and fold mark positions,
# all in mm from the top edge of the page.
DIN5008_FORMS = {
    "A": {"header_height": 27, "fold_marks": (87, 192)},
    "B": {"header_height": 45, "fold_marks": (105, 210)},
}
DIN5008_HOLE_MARK = 148.5
# Letterhead logo: maximum height (mm) per form, see the stylesheet
DIN5008_LOGO_HEIGHTS = {"A": 15, "B": 30}
# Sender line (Rücksendeangabe): separator presets; the setting stores the
# character itself, the names are accepted for values stored by older versions
DIN5008_SENDER_SEPARATORS = {"pipe": "|", "bullet": "•", "middot": "·"}
# Recipient address: font size (pt) and line height (mm), see the stylesheet
DIN5008_ADDRESS_FONT_SIZE = 10
DIN5008_ADDRESS_LINE_HEIGHT = 4.55
# Address window: 20 mm from the left edge, 45 mm high (the 85 mm width is
# fixed in the stylesheet).
DIN5008_ADDRESS_LEFT = 20
DIN5008_ADDRESS_HEIGHT = 45
# Zones inside the address window: sender line (Rücksendeangabe) and
# remark zone (Zusatz- und Vermerkzone) above the recipient address.
DIN5008_SENDER_ZONE_HEIGHT = 5
DIN5008_REMARK_ZONE_HEIGHT = 12.7
# Information block: 125 mm from the left edge, 75 mm wide.
DIN5008_INFO_LEFT = 125
DIN5008_INFO_WIDTH = 75

DIN5008_LAYOUT_KEYS = {
    "layout_din5008.external_layout_din5008_a": "A",
    "layout_din5008.external_layout_din5008_b": "B",
}
DIN5008_PAPERFORMATS = {
    "A": "layout_din5008.paperformat_din5008_a",
    "B": "layout_din5008.paperformat_din5008_b",
}

_ADDRESS_ROW_XPATH = (
    './/div[contains(concat(" ", normalize-space(@class), " "), " address ")]'
)
_INFORMATIONS_XPATH = './/div[@id="informations"]'


def _serialize_fragment(root):
    """Serialize the children of a wrapper element created by lxml."""
    return (root.text or "") + "".join(
        lxml.html.tostring(child, encoding="unicode") for child in root
    )


class LayoutDin5008Mixin(models.AbstractModel):
    """Helpers used by the DIN 5008 report templates.

    The layout templates receive ``company`` either as a ``res.company`` record
    or, in the document layout wizard preview, as the ``base.document.layout``
    record itself. Both models inherit this mixin.
    """

    _name = "layout.din5008.mixin"
    _description = "DIN 5008 Layout Helpers"

    def _layout_din5008_option(self, name):
        """Value of the DIN 5008 setting ``name`` (stored or declared default)."""
        return self._get_report_layout_config_value("din5008." + name)

    def _layout_din5008_separator_char(self):
        """Separator of the sender line: the stored text or a preset name."""
        value = str(self._layout_din5008_option("sender_separator") or "").strip()
        value = DIN5008_SENDER_SEPARATORS.get(value, value)
        return value or DIN5008_SENDER_SEPARATORS["pipe"]

    def _layout_din5008_separator(self):
        """Separator of the sender line text, surrounded by spaces."""
        return f" {self._layout_din5008_separator_char()} "

    def _layout_din5008_separator_markup(self):
        """Separator of the printed sender line with its gap and font scale."""
        styles = []
        gap = self._layout_din5008_option("sender_separator_gap") or 0
        if gap:
            styles.append(f"margin: 0 {gap:g}mm;")
        scale = self._layout_din5008_option("sender_separator_font_scale") or 1
        if scale != 1:
            styles.append(f"font-size: {scale:g}em;")
        style = Markup(' style="%s"') % " ".join(styles) if styles else Markup("")
        return Markup(' <span class="din5008_sender_separator"%s>%s</span> ') % (
            style,
            self._layout_din5008_separator_char(),
        )

    def _layout_din5008_sender_line_plain(self):
        """Sender line (Rücksendeangabe) as plain text.

        The address text of the document layout (with rendered placeholders)
        is printed as a single line, its lines joined by the configured
        separator. Without address text the formatted company address is used.
        """
        self.ensure_one()
        lines = html2plaintext(self._render_company_details() or "").splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        if not lines:
            return self._layout_din5008_format_sender_line()
        return self._layout_din5008_separator().join(lines)

    def _layout_din5008_sender_line(self):
        """Sender line printed above the recipient, as HTML.

        The parts of the plain text line are joined by the separator markup,
        which carries the configured gap and font scale; separators typed in
        the address text (e.g. through the sender line placeholder) are
        styled as well.
        """
        self.ensure_one()
        separator = self._layout_din5008_separator()
        parts = [
            part.strip()
            for part in self._layout_din5008_sender_line_plain().split(separator)
            if part.strip()
        ]
        return self._layout_din5008_separator_markup().join(
            escape(part) for part in parts
        )

    def _layout_din5008_format_sender_line(self):
        """Company name and address fields formatted as a single line."""
        self.ensure_one()
        partner = self.partner_id
        separator = self._layout_din5008_separator()
        indicator = self._layout_din5008_option("sender_country") or "none"
        parts = [self.name or ""]
        if partner:
            country = partner.country_id
            zip_code = partner.zip or ""
            if indicator == "code" and zip_code and country.code:
                zip_code = f"{country.code}-{zip_code}"
            parts += [
                partner.street or "",
                partner.street2 or "",
                " ".join(part for part in (zip_code, partner.city or "") if part),
            ]
            if indicator == "name" and country:
                parts.append(country.name)
        return separator.join(part.strip() for part in parts if part and part.strip())

    def _layout_din5008_scope_class(self):
        """CSS class scoping the company specific rules of one rendered article."""
        self.ensure_one()
        return "din5008_scope_" + re.sub(r"\W", "_", str(self.id))

    def _layout_din5008_geometry(self, form):
        """Return inline styles and CSS for the given DIN 5008 form ('A' or 'B')."""
        self.ensure_one()
        spec = DIN5008_FORMS.get(form) or DIN5008_FORMS["A"]
        option = self._layout_din5008_option
        offset_top = option("address_offset_top") or 0
        address_height = option("address_height") or DIN5008_ADDRESS_HEIGHT
        info_left = option("info_left") or DIN5008_INFO_LEFT
        info_width = option("info_width") or DIN5008_INFO_WIDTH
        remark_height = option("remark_zone_height") or 0
        recipient_top = DIN5008_SENDER_ZONE_HEIGHT + remark_height
        font_scale = option("address_font_scale") or 1
        logo_height = option("logo_height") or 0
        scope = f".o_layout_din5008.{self._layout_din5008_scope_class()}"
        company_css = (
            f"{scope} .address.row {{ margin-top: {offset_top}mm; "
            f"min-height: {address_height}mm; }}\n"
            f"{scope} .address.row > div[name='address'] "
            f"{{ padding-top: {recipient_top:g}mm; }}\n"
            f"{scope} .address.row > div[name='information_block'], "
            f"{scope} .address.row > .din5008_informations "
            f"{{ margin-left: {info_left - DIN5008_ADDRESS_LEFT}mm; "
            f"width: {info_width}mm; }}\n"
        )
        if font_scale != 1:
            company_css += (
                f"{scope} .address.row > div[name='address'] "
                f"{{ font-size: {DIN5008_ADDRESS_FONT_SIZE * font_scale:g}pt; "
                f"line-height: {DIN5008_ADDRESS_LINE_HEIGHT * font_scale:g}mm; }}\n"
            )
        return {
            "header": f"height: {spec['header_height']}mm;",
            "logo": f"max-height: {logo_height}mm;" if logo_height else None,
            "sender_line": f"top: {offset_top}mm;",
            "fold_marks": [f"top: {top}mm;" for top in spec["fold_marks"]],
            "hole_mark": f"top: {DIN5008_HOLE_MARK}mm;",
            "company_css": Markup(company_css),
        }

    def _layout_din5008_relocate_informations(self, address_html, body):
        """Move the ``#informations`` block of the report body into the address row.

        Standard reports render the document information (dates, references,
        ...) as ``<div id="informations">`` below the title. In the "beside"
        mode this block is moved into the DIN 5008 information block next to
        the address window. Both arguments are already rendered HTML; only
        these fragments are parsed, the surrounding document is untouched.

        :return: tuple ``(address_html, body_html)`` as Markup
        """
        address_html = str(address_html or "")
        body_html = str(body or "")
        if 'id="informations"' not in body_html or not address_html.strip():
            return Markup(address_html), Markup(body_html)
        body_root = lxml.html.fragment_fromstring(body_html, create_parent="div")
        address_root = lxml.html.fragment_fromstring(address_html, create_parent="div")
        informations = body_root.xpath(_INFORMATIONS_XPATH)
        rows = address_root.xpath(_ADDRESS_ROW_XPATH)
        if not informations or not rows:
            return Markup(address_html), Markup(body_html)
        node = informations[0]
        node.drop_tree()
        node.tail = None
        container = lxml.html.Element(
            "div", {"class": "din5008_informations", "name": "din5008_informations"}
        )
        container.append(node)
        rows[0].append(container)
        return (
            Markup(_serialize_fragment(address_root)),
            Markup(_serialize_fragment(body_root)),
        )
