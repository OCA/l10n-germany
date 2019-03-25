# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def l10n_de_add_move_in_statement(self):
        for move in self:
            move.l10n_de_tax_statement_include = True
        self._l10n_de_statement_update()

    def l10n_de_unlink_move_from_statement(self):
        for move in self:
            move.l10n_de_tax_statement_include = False
        self._l10n_de_statement_update()

    def _l10n_de_statement_update(self):
        model = self.env.context.get('params', {}).get('model', '')
        obj_id = self.env.context.get('params', {}).get('id')
        if model == 'l10n.de.tax.statement' and isinstance(obj_id, int):
            statement = self.env['l10n.de.tax.statement'].browse(obj_id)
            statement.statement_update()
