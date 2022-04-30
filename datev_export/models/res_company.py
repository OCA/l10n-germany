# Copyright (C) 2023 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    datev_consultant_number = fields.Char(
        "Consultant Number",
        size=8,
        help="Number from 1000 to 99999999",
    )

    datev_client_number = fields.Char(
        "Client Number",
        size=5,
        help="Number from 0 to 99999",
    )

    datev_account_code_length = fields.Integer(
        "DATEV account code length",
        default=5,
    )
