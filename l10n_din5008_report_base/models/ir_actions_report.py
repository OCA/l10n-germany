# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
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

    def _build_wkhtmltopdf_args(
        self,
        paperformat_id,
        landscape,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        specific_paperformat_args = dict(specific_paperformat_args or {})

        company = self.env.company
        din5008_layout = self.env.ref(
            "l10n_din5008.external_layout_din5008",
            raise_if_not_found=False,
        )
        margin_bottom = company._get_din5008_config_value(
            "page",
            "margin_bottom",
            default=40.0,
        )

        if (
            din5008_layout
            and company.external_report_layout_id.id == din5008_layout.id
            and margin_bottom is not None
        ):
            specific_paperformat_args["data-report-margin-bottom"] = margin_bottom

        return super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )

    @staticmethod
    def _marks_overlay(box, marks):
        """Create a PDF page with DIN 5008 marks."""
        width = float(box.getUpperRight_x() - box.getLowerLeft_x())
        height = float(box.getUpperRight_y() - box.getLowerLeft_y())
        top = float(box.getUpperRight_y())
        mm = 72 / 25.4
        mark_height = 0.2 * mm
        left_margin = 1 * mm
        marker = " ".join(
            f"{left_margin:.2f} {top - y * mm:.2f} "
            f"{length * mm:.2f} {mark_height:.2f} re f"
            for y, length in marks
        )
        content = DecodedStreamObject()
        content.setData(f"q 0 g {marker} Q".encode("ascii"))
        overlay = PageObject.createBlankPage(width=width, height=height)
        overlay[NameObject("/Contents")] = content
        overlay[NameObject("/Resources")] = DictionaryObject()

        return overlay

    @api.model
    def _run_wkhtmltopdf(
        self,
        bodies,
        report_ref=False,
        *args,
        **kwargs,
    ):
        pdf = super()._run_wkhtmltopdf(
            bodies,
            report_ref,
            *args,
            **kwargs,
        )
        marks = self._din5008_marks(report_ref)

        if not marks:
            return pdf

        return self._din5008_stamp(
            pdf,
            marks,
        )

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
            "l10n_din5008.paperformat_euro_din_a": (
                (87, 4),
                (192, 4),
            ),
            "l10n_din5008.paperformat_euro_din": (
                (105, 4),
                (210, 4),
            ),
        }
        hole_mark = (148.5, 6)

        for xmlid, folds in fold_marks.items():
            paperformat_ref = self.env.ref(
                xmlid,
                raise_if_not_found=False,
            )
            if paperformat_ref != paperformat:
                continue

            marks = []

            if company._get_din5008_config_value(
                "marks",
                "fold_marker",
                default=True,
            ):
                marks.extend(folds)

            if company._get_din5008_config_value(
                "marks",
                "hole_marker",
                default=True,
            ):
                marks.append(hole_mark)

            return marks

        return []

    @api.model
    def _din5008_stamp(self, pdf, marks):
        writer = PdfWriter()
        reader = PdfReader(io.BytesIO(pdf))

        for page in reader.pages:
            page.mergePage(
                self._marks_overlay(
                    page.mediaBox,
                    marks,
                )
            )
            writer.addPage(page)

        output = io.BytesIO()
        writer.write(output)

        return output.getvalue()
