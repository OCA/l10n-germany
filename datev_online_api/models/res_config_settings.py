# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    datev_api = fields.Selection(
        related="company_id.datev_api",
        readonly=False,
    )
    datev_api_long_term = fields.Boolean(
        related="company_id.datev_api_long_term",
        readonly=False,
    )
    datev_api_client_id = fields.Char(
        related="company_id.datev_api_client_id",
        readonly=False,
    )
    datev_api_client_secret = fields.Char(
        related="company_id.datev_api_client_secret",
        readonly=False,
    )
    datev_api_refresh_token_expire = fields.Datetime(
        related="company_id.datev_api_refresh_token_expire"
    )
    datev_api_service_ids = fields.Many2many(related="company_id.datev_api_service_ids")

    def action_datev_api_authorization(self):
        return self.company_id.action_datev_api_authorization()

    def action_datev_api_revoke(self):
        return self.company_id.action_datev_api_revoke()
