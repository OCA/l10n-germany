# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class IrActionsReportDin5008(models.Model):
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
        if (
            din5008_layout
            and company.external_report_layout_id.id == din5008_layout.id
            and company.l10n_din5008_margin_bottom
        ):
            specific_paperformat_args["data-report-margin-bottom"] = (
                company.l10n_din5008_margin_bottom
            )

        return super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
