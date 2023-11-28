# Copyright (C) 2023 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    datev_consultant_number = fields.Char(
        related="company_id.datev_consultant_number", readonly=False,
    )

    datev_client_number = fields.Char(
        related="company_id.datev_client_number", readonly=False,
    )
