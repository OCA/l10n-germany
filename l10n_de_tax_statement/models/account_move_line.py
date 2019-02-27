# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_de_tax_statement_id = fields.Many2one(
        related='move_id.l10n_de_tax_statement_id',
        store=True,
        readonly=True,
        string='Related Move Statement'
    )
    l10n_de_tax_statement_include = fields.Boolean(
        related='move_id.l10n_de_tax_statement_include',
        store=True,
        readonly=True
    )
