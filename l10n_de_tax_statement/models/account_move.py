# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_de_tax_statement_id = fields.Many2one(
        "l10n.de.tax.statement", "statement", copy=False
    )
    l10n_de_tax_statement_include = fields.Boolean(
        "Include in VAT Statement", copy=False
    )

    def l10n_de_add_move_in_statement(self):
        self.write({"l10n_de_tax_statement_include": True})

    def l10n_de_unlink_move_from_statement(self):
        self.write({"l10n_de_tax_statement_include": False})
