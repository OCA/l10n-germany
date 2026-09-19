# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io

from odoo import api, models
from odoo.tools.pdf import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    PageObject,
    PdfReader,
    PdfWriter,
)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @staticmethod
    def _marks_overlay(box, marks):
        """Creates a PDF page with DIN 5008 marks."""
        width = float(box.getUpperRight_x() - box.getLowerLeft_x())
        height = float(box.getUpperRight_y() - box.getLowerLeft_y())
        top = float(box.getUpperRight_y())
        mm = 72 / 25.4
        mark_height = 0.2 * mm
        marker = " ".join(
            f"0.00 {top - y * mm:.2f} {length * mm:.2f} {mark_height:.2f} re f"
            for y, length in marks
        )
        content = DecodedStreamObject()
        content.setData(f"q 0 g {marker} Q".encode("ascii"))
        overlay = PageObject.createBlankPage(width=width, height=height)
        overlay[NameObject("/Contents")] = content
        overlay[NameObject("/Resources")] = DictionaryObject()
        return overlay

    @api.model
    def _run_wkhtmltopdf(self, bodies, report_ref=False, *args, **kwargs):
        pdf = super()._run_wkhtmltopdf(bodies, report_ref, *args, **kwargs)
        marks = self._din5008_marks(report_ref)
        return self._din5008_stamp(pdf, marks) if marks else pdf

    @api.model
    def _din5008_marks(self, report_ref):
        company = self.env.company
        report = self._get_report(report_ref) if report_ref else None
        paperformat = (
            report.paperformat_id
            if report and report.paperformat_id
            else company.paperformat_id
        )
        fold_marks = {
            "l10n_din5008.paperformat_euro_din_a": ((87, 5), (192, 5)),
            "l10n_din5008.paperformat_euro_din": ((105, 5), (210, 5)),
        }
        hole_mark = (148.5, 8)

        for xmlid, folds in fold_marks.items():
            if self.env.ref(xmlid, raise_if_not_found=False) != paperformat:
                continue

            marks = list(folds) if company.l10n_din5008_fold_marker else []
            if company.l10n_din5008_hole_marker:
                marks.append(hole_mark)
            return marks

        return []

    @api.model
    def _din5008_stamp(self, pdf, marks):
        writer = PdfWriter()
        for page in PdfReader(io.BytesIO(pdf)).pages:
            page.mergePage(self._marks_overlay(page.mediaBox, marks))
            writer.addPage(page)

        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
