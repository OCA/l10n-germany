# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from ..models.res_company import REPORT_FOOTER_RENDER_MODEL


class BaseDocumentLayout(models.TransientModel):
    _name = "base.document.layout"
    _inherit = ["base.document.layout", "report.layout.config.mixin"]

    report_layout_config = fields.Json(
        related="company_id.report_layout_config", readonly=False
    )
    # settings offered for the selected layout, rendered by the widget
    report_layout_config_fields = fields.Json(
        compute="_compute_report_layout_config_fields"
    )
    # model offered by the dynamic placeholder picker of the footer editor
    report_footer_render_model = fields.Char(default=REPORT_FOOTER_RENDER_MODEL)

    @api.depends("report_layout_id")
    def _compute_report_layout_config_fields(self):
        for wizard in self:
            wizard.report_layout_config_fields = wizard.get_report_layout_config_fields(
                wizard.report_layout_id.view_id.key
            )

    def _get_company_placeholder_overrides(self):
        """Placeholder values taken from the wizard instead of the company.

        Meant to be extended for values that depend on unsaved wizard fields.
        """
        self.ensure_one()
        return {}

    def _render_wizard_placeholders(self, template):
        return self.env["res.company"]._render_company_placeholders(
            template, self.company_id, self._get_company_placeholder_overrides()
        )

    def _render_report_footer(self):
        """Footer of the wizard with rendered placeholders (layout preview)."""
        self.ensure_one()
        return self._render_wizard_placeholders(self.report_footer)

    def _render_company_details(self):
        self.ensure_one()
        return self._render_wizard_placeholders(self.company_details)

    def _render_report_header(self):
        self.ensure_one()
        return self._render_wizard_placeholders(self.report_header)

    @api.depends("report_layout_config")
    def _compute_preview(self):
        return super()._compute_preview()
