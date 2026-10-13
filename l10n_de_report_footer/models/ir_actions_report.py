# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _get_rendering_context(self, report, docids, data):
        """Expose the configured bottom margin to the report layout.

        ``web.report_layout`` writes it as ``data-report-margin-bottom`` on the
        root tag, which ``_build_wkhtmltopdf_args`` forwards to wkhtmltopdf.
        """
        data = super()._get_rendering_context(report, docids, data)
        margin = self.env.company._get_report_footer_margin_bottom()
        if margin:
            data.setdefault("data_report_margin_bottom", margin)
        return data
