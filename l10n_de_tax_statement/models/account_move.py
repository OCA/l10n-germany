# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_de_tax_statement_id = fields.Many2one(
        'l10n.de.tax.statement',
        'Statement'
    )
    l10n_de_tax_statement_include = fields.Boolean(
        'Include in VAT Statement'
    )

    def add_move_in_statement(self):
        for move in self:
            move.l10n_de_tax_statement_include = True

    def unlink_move_from_statement(self):
        for move in self:
            move.l10n_de_tax_statement_include = False
