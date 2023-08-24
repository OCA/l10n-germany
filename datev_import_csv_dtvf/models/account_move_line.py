# Copyright 2017-2019 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    import_external_id = fields.Char(
        help="Can be used to tag imported move."
        " Delete all importred move if need (error on file imported)"
    )
    indicator = fields.Char(
        help="Can be used to decide Soll/Haben-Kennzeichen,"
        "to decide credit or debit entry in first move line."
        "if 'S' then fill 'Credit' value in first move line OR "
        "if 'H' then 'Debit' value in first move line",
    )
