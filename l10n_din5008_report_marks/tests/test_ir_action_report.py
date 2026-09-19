# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
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
        cls.report = cls.env["ir.actions.report"].search([], limit=1)

    def test_din5008_marks_a_fold_and_hole(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = True
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [(87, 5), (192, 5), (148.5, 8)])

    def test_din5008_marks_a_fold_only(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = False
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [(87, 5), (192, 5)])

    def test_din5008_marks_a_hole_only(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_fold_marker = False
        self.company.l10n_din5008_hole_marker = True
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [(148.5, 8)])

    def test_din5008_marks_disabled(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_fold_marker = False
        self.company.l10n_din5008_hole_marker = False
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [])

    def test_din5008_marks_b(self):
        self.company.paperformat_id = self.paperformat_b
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = True
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [(105, 5), (210, 5), (148.5, 8)])

    def test_din5008_marks_unknown_paperformat(self):
        paperformat = self.env["report.paperformat"].create(
            {"name": "DIN 5008 Test", "format": "A4"}
        )
        self.company.paperformat_id = paperformat
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = True
        marks = self.report._din5008_marks(False)
        self.assertEqual(marks, [])

    def test_din5008_marks_report_paperformat(self):
        self.company.paperformat_id = self.paperformat_b
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = True
        report = self.env["ir.actions.report"].create(
            {
                "name": "DIN 5008 Test Report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "base.report_partnercard",
                "paperformat_id": self.paperformat_a.id,
            }
        )
        marks = self.report._din5008_marks(report.id)
        self.assertEqual(marks, [(87, 5), (192, 5), (148.5, 8)])

    def test_din5008_marks_report_without_paperformat(self):
        self.company.paperformat_id = self.paperformat_a
        self.company.l10n_din5008_fold_marker = True
        self.company.l10n_din5008_hole_marker = True
        report = self.env["ir.actions.report"].create(
            {
                "name": "DIN 5008 Test Report",
                "model": "res.partner",
                "report_type": "qweb-pdf",
                "report_name": "base.report_partnercard",
            }
        )
        marks = self.report._din5008_marks(report.id)
        self.assertEqual(marks, [(87, 5), (192, 5), (148.5, 8)])

    def test_marks_overlay(self):
        page = PageObject.createBlankPage(width=595.28, height=841.89)
        overlay = self.report._marks_overlay(
            page.mediaBox,
            [(87, 5), (148.5, 8)],
        )
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
        self.assertIn(b"0.00 595.28 14.17 0.57 re f", content)
        self.assertIn(b"0.00 420.95 22.68 0.57 re f", content)

    def test_marks_overlay_without_marks(self):
        page = PageObject.createBlankPage(width=595.28, height=841.89)
        overlay = self.report._marks_overlay(page.mediaBox, [])
        content = overlay.getContents().getData()
        self.assertEqual(content, b"q 0 g  Q")

    def test_din5008_stamp_one_page(self):
        writer = PdfWriter()
        writer.addPage(PageObject.createBlankPage(width=595.28, height=841.89))
        pdf = io.BytesIO()
        writer.write(pdf)
        stamped = self.report._din5008_stamp(pdf.getvalue(), [(87, 5)])
        reader = PdfReader(io.BytesIO(stamped))
        self.assertEqual(reader.getNumPages(), 1)
        content = reader.getPage(0).getContents().getData()
        self.assertIn(b"0 595.28 14.17 0.57 re", content)
        self.assertIn(b"f", content)

    def test_din5008_stamp_all_pages(self):
        writer = PdfWriter()
        for _ in range(3):
            writer.addPage(PageObject.createBlankPage(width=595.28, height=841.89))

        pdf = io.BytesIO()
        writer.write(pdf)
        stamped = self.report._din5008_stamp(pdf.getvalue(), [(87, 5), (192, 5)])
        reader = PdfReader(io.BytesIO(stamped))
        self.assertEqual(reader.getNumPages(), 3)
        for page_number in range(reader.getNumPages()):
            content = reader.getPage(page_number).getContents().getData()
            self.assertIn(b"0 595.28 14.17 0.57 re", content)
            self.assertIn(b"0 297.64 14.17 0.57 re", content)
            self.assertIn(b"f", content)

    def test_run_wkhtmltopdf_with_marks(self):
        pdf = b"rendered pdf"
        marks = [(87, 5)]
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

    def test_run_wkhtmltopdf_forwards_args_and_kwargs(self):
        pdf = b"rendered pdf"
        marks = [(87, 5)]

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
            result = self.report._run_wkhtmltopdf([], False, "extra", test=True)

        run_wkhtmltopdf.assert_called_once_with([], False, "extra", test=True)
        get_marks.assert_called_once_with(False)
        stamp.assert_called_once_with(pdf, marks)
        self.assertEqual(result, b"stamped pdf")
