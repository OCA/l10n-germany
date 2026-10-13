# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from unittest.mock import patch

from odoo.tools.pdf import PageObject, PdfReader, PdfWriter

from odoo.addons.base.models.ir_actions_report import (
    IrActionsReport as BaseIrActionsReport,
)
from odoo.addons.base.tests.common import BaseCommon


class TestIrActionsReport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.paperformat_a = cls.env.ref("l10n_din5008.paperformat_euro_din_a")
        cls.paperformat_b = cls.env.ref("l10n_din5008.paperformat_euro_din")
        cls.din5008_layout = cls.env.ref("l10n_din5008.external_layout_din5008")
        cls.standard_layout = cls.env.ref("web.external_layout_standard")
        cls.report = cls.env["ir.actions.report"].search([], limit=1)

    def _set_marks_config(self, fold_marker=True, hole_marker=True):
        self.company.l10n_din5008_config = {
            "marks": {"fold_marker": fold_marker, "hole_marker": hole_marker}
        }

    def _make_pdf(self, page_count=1):
        writer = PdfWriter()
        for _ in range(page_count):
            writer.addPage(PageObject.createBlankPage(width=595.28, height=841.89))

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

    def test_din5008_marks_a(self):
        self.company.paperformat_id = self.paperformat_a
        self._set_marks_config()
        self.assertEqual(
            self.report._din5008_marks(False), [(87, 4), (192, 4), (148.5, 6)]
        )
        self._set_marks_config(fold_marker=False, hole_marker=False)
        self.assertEqual(self.report._din5008_marks(False), [])

    def test_din5008_marks_default_config(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_config = {}
        self.assertEqual(
            self.report._din5008_marks(False), [(87, 4), (192, 4), (148.5, 6)]
        )

    def test_din5008_marks_b(self):
        self.company.paperformat_id = self.paperformat_b
        self._set_marks_config()
        self.assertEqual(
            self.report._din5008_marks(False), [(105, 4), (210, 4), (148.5, 6)]
        )

    def test_din5008_marks_unknown_paperformat(self):
        paperformat = self.env["report.paperformat"].create(
            {"name": "DIN 5008 Test", "format": "A4"}
        )
        self.company.paperformat_id = paperformat
        self._set_marks_config()
        self.assertEqual(self.report._din5008_marks(False), [])

    def test_din5008_marks_report_paperformat(self):
        self.company.paperformat_id = self.paperformat_b
        self._set_marks_config()
        report = self.env["ir.actions.report"].create(
            {
                "name": "DIN 5008 Test Report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "base.report_partnercard",
                "paperformat_id": self.paperformat_a.id,
            }
        )
        self.assertEqual(
            self.report._din5008_marks(report.id), [(87, 4), (192, 4), (148.5, 6)]
        )

    def test_marks_overlay(self):
        page = PageObject.createBlankPage(width=595.28, height=841.89)
        overlay = self.report._marks_overlay(page.mediaBox, [(87, 5), (148.5, 8)])
        self.assertEqual(
            float(overlay.mediaBox.getUpperRight_x()),
            float(page.mediaBox.getUpperRight_x()),
        )
        self.assertEqual(
            float(overlay.mediaBox.getUpperRight_y()),
            float(page.mediaBox.getUpperRight_y()),
        )
        content = overlay.getContents().getData()
        self.assertIn(b"0 g", content)
        self.assertIn(b"2.83 595.28 14.17 0.57 re f", content)
        self.assertIn(b"2.83 420.95 22.68 0.57 re f", content)

    def test_din5008_stamp_one_page(self):
        pdf = self._make_pdf()
        stamped = self.report._din5008_stamp(pdf, [(87, 4)])
        reader = PdfReader(io.BytesIO(stamped))
        self.assertEqual(reader.getNumPages(), 1)
        content = reader.getPage(0).getContents().getData()
        self.assertIn(b"re", content)
        self.assertIn(b"f", content)

    def test_din5008_stamp_all_pages(self):
        pdf = self._make_pdf(page_count=3)
        stamped = self.report._din5008_stamp(pdf, [(87, 4), (192, 4)])
        reader = PdfReader(io.BytesIO(stamped))
        self.assertEqual(reader.getNumPages(), 3)

        for page_number in range(reader.getNumPages()):
            content = reader.getPage(page_number).getContents().getData()
            self.assertIn(b"re", content)
            self.assertIn(b"f", content)

    def test_build_args_din5008_default_margin(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_config = {}
        model = self.env["ir.actions.report"]

        with patch.object(
            BaseIrActionsReport,
            "_build_wkhtmltopdf_args",
            return_value=[],
        ) as build_args:
            model._build_wkhtmltopdf_args(self.paperformat_a, False)

        self.assertEqual(
            build_args.call_args.kwargs["specific_paperformat_args"],
            {"data-report-margin-bottom": 40.0},
        )

    def test_build_args_custom_margin(self):
        self.company.external_report_layout_id = self.din5008_layout
        self.company.l10n_din5008_config = {"page": {"margin_bottom": 55.0}}
        model = self.env["ir.actions.report"]

        with patch.object(
            BaseIrActionsReport,
            "_build_wkhtmltopdf_args",
            return_value=[],
        ) as build_args:
            model._build_wkhtmltopdf_args(
                self.paperformat_a,
                False,
                specific_paperformat_args={"data-report-margin-top": 12.0},
                set_viewport_size=True,
            )

        self.assertEqual(
            build_args.call_args.kwargs["specific_paperformat_args"],
            {"data-report-margin-top": 12.0, "data-report-margin-bottom": 55.0},
        )
        self.assertTrue(build_args.call_args.kwargs["set_viewport_size"])

    def test_build_args_other_layout(self):
        self.company.external_report_layout_id = self.standard_layout
        self.company.l10n_din5008_config = {"page": {"margin_bottom": 55.0}}
        model = self.env["ir.actions.report"]

        with patch.object(
            BaseIrActionsReport,
            "_build_wkhtmltopdf_args",
            return_value=[],
        ) as build_args:
            model._build_wkhtmltopdf_args(
                self.paperformat_a,
                False,
                specific_paperformat_args={"data-report-margin-top": 12.0},
            )

        self.assertEqual(
            build_args.call_args.kwargs["specific_paperformat_args"],
            {"data-report-margin-top": 12.0},
        )

    def test_run_wkhtmltopdf_with_marks(self):
        pdf = b"rendered pdf"
        marks = [(87, 4)]

        with (
            patch.object(
                BaseIrActionsReport,
                "_run_wkhtmltopdf",
                return_value=pdf,
            ) as run_wkhtmltopdf,
            patch.object(
                type(self.report),
                "_din5008_marks",
                return_value=marks,
            ) as get_marks,
            patch.object(
                type(self.report),
                "_din5008_stamp",
                return_value=b"stamped pdf",
            ) as stamp,
        ):
            result = self.report._run_wkhtmltopdf([], False)

        run_wkhtmltopdf.assert_called_once_with([], False)
        get_marks.assert_called_once_with(False)
        stamp.assert_called_once_with(pdf, marks)
        self.assertEqual(result, b"stamped pdf")

    def test_run_wkhtmltopdf_without_marks(self):
        pdf = b"rendered pdf"

        with (
            patch.object(
                BaseIrActionsReport,
                "_run_wkhtmltopdf",
                return_value=pdf,
            ) as run_wkhtmltopdf,
            patch.object(
                type(self.report),
                "_din5008_marks",
                return_value=[],
            ) as get_marks,
            patch.object(
                type(self.report),
                "_din5008_stamp",
            ) as stamp,
        ):
            result = self.report._run_wkhtmltopdf([], False)

        run_wkhtmltopdf.assert_called_once_with([], False)
        get_marks.assert_called_once_with(False)
        stamp.assert_not_called()
        self.assertEqual(result, pdf)
