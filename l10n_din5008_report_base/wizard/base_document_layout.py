# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    l10n_din5008_config = fields.Json(
        string="DIN 5008 Configuration",
        related="company_id.l10n_din5008_config",
        readonly=False,
    )

    l10n_din5008_config_modified = fields.Boolean(
        string="DIN 5008 Configuration Modified",
        compute="_compute_l10n_din5008_config_modified",
    )

    def _get_din5008_config(self):
        self.ensure_one()
        preview_config = self.env.context.get("l10n_din5008_preview_config")
        if preview_config is not None:
            return preview_config
        return self.l10n_din5008_config or {}

    @api.model
    def action_get_din5008_preview(self, wizard_values, config):
        """Render the preview using the current unsaved DIN 5008 settings."""
        if not isinstance(wizard_values, dict):
            wizard_values = {}
        if not isinstance(config, dict):
            config = {}

        allowed_fields = {
            "company_id",
            "report_layout_id",
            "external_report_layout_id",
            "paperformat_id",
            "logo",
            "font",
            "primary_color",
            "secondary_color",
            "report_header",
            "report_footer",
            "layout_background",
            "layout_background_image",
            "company_details",
            "qr_code",
            "account_number",
        }

        values = {
            key: value for key, value in wizard_values.items() if key in allowed_fields
        }

        wizard = self.create(values)
        wizard = wizard.with_context(
            l10n_din5008_preview_config=config,
            bin_size=False,
        )
        wizard._compute_preview()
        return wizard.preview or ""

    def _get_din5008_config_value(self, *keys, default=None):
        self.ensure_one()
        value = self._get_din5008_config()

        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)

        return default if value is None else value

    @api.depends("l10n_din5008_config")
    def _compute_l10n_din5008_config_modified(self):
        for record in self:
            record.l10n_din5008_config_modified = bool(record.l10n_din5008_config)

    @api.onchange("paperformat_id", "l10n_din5008_config")
    def _onchange_din5008_report_config(self):
        self._compute_preview()

    def action_reset_din5008_config(self):
        self.ensure_one()

        self.company_id.write(
            {
                "l10n_din5008_config": {},
            }
        )

        return True
