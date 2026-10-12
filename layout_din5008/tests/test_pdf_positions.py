# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import io
import unittest

from odoo.tests import HttpCase, tagged
from odoo.tools.pdf import PdfFileReader

from .common import LayoutDin5008Common
from .pdf_tools import extract_positions, find_marks, find_text

PAGE_HEIGHT = 297
LINE = 4.55  # recipient line height in mm
BASELINE_TOLERANCE = 5.5  # baseline of a text line lies below the top of its box


@tagged("post_install", "-at_install")
class TestPdfPositions(LayoutDin5008Common, HttpCase):
    """Render real PDFs and check the DIN 5008 positions in millimetres."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.env["ir.actions.report"].get_wkhtmltopdf_state() != "ok":
            raise unittest.SkipTest("wkhtmltopdf is not available")
        cls._setup_din5008()
        cls.env["ir.config_parameter"].sudo().set_param("report.url", cls.base_url())

    def _render_pages(self, data=None):
        pdf = self.report.with_context(force_report_rendering=True)._render_qweb_pdf(
            self.report.id, self.partner.ids, data=data
        )[0]
        reader = PdfFileReader(io.BytesIO(pdf))
        return [extract_positions(page) for page in reader.pages]

    def _assert_marks(self, rects, expected):
        marks = find_marks(rects)
        self.assertEqual(len(marks), len(expected), marks)
        for (top, width), (expected_top, expected_width) in zip(
            marks, expected, strict=True
        ):
            self.assertAlmostEqual(top, expected_top, delta=1.0)
            self.assertAlmostEqual(width, expected_width, delta=1.0)

    def _assert_box(self, position, x, top, height=LINE, label=""):
        actual_x, actual_top = position
        self.assertAlmostEqual(actual_x, x, delta=1.5, msg=f"{label} x")
        self.assertGreaterEqual(actual_top, top - 0.5, msg=f"{label} top")
        self.assertLessEqual(
            actual_top, top + height + BASELINE_TOLERANCE, msg=f"{label} top"
        )

    def _check_form(self, form, header, remark_zone=0):
        self._set_form(form)
        self._write_config(
            {
                "din5008.informations_position": "below",
                "din5008.remark_zone_height": remark_zone,
            }
        )
        texts, rects = self._render_pages()[0]
        # sender line inside the 5 mm zone at the top of the address window
        self._assert_box(
            find_text(texts, "Acme GmbH |"), 25, header, height=5, label="sender line"
        )
        # recipient starts below the sender zone (5 mm) and the remark zone
        self._assert_box(
            find_text(texts, "Max Mustermann"),
            25,
            header + 5 + remark_zone,
            label="recipient",
        )
        # information block 125 mm from the left edge, 5 mm below the window top
        self._assert_box(
            find_text(texts, "Shipping Address"), 125, header + 5, label="info block"
        )
        # title two lines below the address window
        title_x, title_top = find_text(texts, "Rechnung")
        self.assertAlmostEqual(title_x, 25, delta=1.5)
        self.assertGreaterEqual(title_top, header + 45 + 8.46)
        self.assertLessEqual(title_top, header + 45 + 8.46 + 12)
        # document information below the title (standard position)
        info_x, info_top = find_text(texts, "Rechnungsdatum")
        self.assertAlmostEqual(info_x, 25, delta=1.5)
        self.assertGreater(info_top, title_top)
        # footer inside the bottom margin
        footer_x, footer_top = find_text(texts, "Tel. +49")
        self.assertGreaterEqual(footer_top, PAGE_HEIGHT - 30)
        self.assertLessEqual(footer_top, PAGE_HEIGHT)
        return texts, rects

    def test_form_a(self):
        texts, rects = self._check_form("A", 27)
        self._assert_marks(rects, [(87, 5), (148.5, 8), (192, 5)])

    def test_form_b(self):
        # Form B with the DIN 5008 remark zone: recipient at 62.7 mm
        texts, rects = self._check_form("B", 45, remark_zone=12.7)
        self._assert_marks(rects, [(105, 5), (148.5, 8), (210, 5)])

    def test_informations_beside(self):
        texts, rects = self._render_pages()[0]
        self._assert_box(
            find_text(texts, "Shipping Address"), 125, 27 + 5, label="info block"
        )
        info_x, info_top = find_text(texts, "Rechnungsdatum")
        self.assertAlmostEqual(info_x, 125, delta=1.5)
        self.assertGreater(info_top, 27 + 5)
        self.assertLess(info_top, 27 + 45)
        title_x, title_top = find_text(texts, "Rechnung")
        self.assertGreaterEqual(title_top, 27 + 45 + 8.46)

    def test_long_content_pushes_title(self):
        """A long information block moves the title down instead of overlapping."""
        self._write_config({"din5008.address_height": 20})
        texts, rects = self._render_pages()[0]
        last_info_top = max(top for text, _, top in texts if text in ("K-4711",))
        title_x, title_top = find_text(texts, "Rechnung")
        self.assertGreater(title_top, last_info_top + 4)

    def test_margin_bottom_and_second_page(self):
        self._write_config({"page.margin_bottom": 40})
        pages = self._render_pages(data={"n_rows": 40})
        self.assertGreaterEqual(len(pages), 2)
        for texts, rects in pages:
            footer_x, footer_top = find_text(texts, "Tel. +49")
            # footer text is the last block of the enlarged footer area
            self.assertGreaterEqual(footer_top, PAGE_HEIGHT - 40)
            self.assertLessEqual(footer_top, PAGE_HEIGHT - 5)
            self._assert_marks(rects, [(87, 5), (148.5, 8), (192, 5)])
        # body content stays above the enlarged footer
        for texts, _ in pages:
            body_bottom = max(
                top for text, _, top in texts if text.startswith("Position")
            )
            self.assertLessEqual(body_bottom, PAGE_HEIGHT - 40)
