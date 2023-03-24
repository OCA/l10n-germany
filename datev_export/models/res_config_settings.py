# Copyright (C) 2023 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    datev_consultant_number = fields.Char(
        related="company_id.datev_consultant_number",
        readonly=False,
    )

    datev_client_number = fields.Char(
        related="company_id.datev_client_number",
        readonly=False,
    )

    datev_account_code_length = fields.Integer(
        related="company_id.datev_account_code_length",
        readonly=False,
    )

    datev_partner_numbering = fields.Selection(
        related="company_id.datev_partner_numbering", readonly=False
    )

    datev_customer_sequence_id = fields.Many2one(
        related="company_id.datev_customer_sequence_id", readonly=False
    )

    datev_supplier_sequence_id = fields.Many2one(
        related="company_id.datev_supplier_sequence_id", readonly=False
    )
