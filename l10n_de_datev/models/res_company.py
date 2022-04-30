# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    datev_consultant_id = fields.Char(size=7, string="DATEV consultant ID")
    datev_client_id = fields.Char(size=5, string="DATEV client ID")
    datev_account_code_length = fields.Integer("DATEV account code length")
