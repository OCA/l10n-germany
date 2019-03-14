# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def get_move_line_partial_domain(self, from_date, to_date, company_id):
        res = super(AccountTax, self).get_move_line_partial_domain(
            from_date,
            to_date,
            company_id
        )

        if not self.env.context.get('skip_invoice_basis_domain'):
            return res

        if not self.env.context.get('unreported_move'):
            return res

        # Both 'skip_invoice_basis_domain' and 'unreported_move' must be set
        # in context, in order to get the domain for the unreported invoices
        return expression.AND([
            [('company_id', '=', company_id)],
            [('l10n_de_tax_statement_id', '=', False)],
            [('l10n_de_tax_statement_include', '=', True)],
            self._get_move_line_tax_date_range_domain(from_date),
        ])

    @api.model
    def _get_move_line_tax_date_range_domain(self, from_date):
        unreported_date = self.env.context.get('unreported_move_from_date')
        res = [
            ('date', '<', from_date),
        ]
        if unreported_date:
            res += [
                ('date', '>=', unreported_date),
            ]
        return res

    def get_balance_domain(self, state_list, type_list):
        res = super().get_balance_domain(state_list, type_list)
        tax_ids = self.env.context.get('l10n_de_statement_tax_ids')
        if tax_ids:
            for item in res:
                if item[0] == 'tax_line_id':
                    res.remove(item)
            res.append(
                ('tax_line_id', 'in', tax_ids)
            )
        return res

    def get_base_balance_domain(self, state_list, type_list):
        res = super().get_base_balance_domain(state_list, type_list)
        tax_ids = self.env.context.get('l10n_de_statement_tax_ids')
        if tax_ids:
            for item in res:
                if item[0] == 'tax_ids':
                    res.remove(item)
            res.append(
                ('tax_ids', 'in', tax_ids)
            )
        return res
