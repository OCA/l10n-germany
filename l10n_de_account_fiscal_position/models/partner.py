# Copyright 2019 Nikolina Todorova <nikolina.todorova@initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    @api.model
    def map_accounts(self, accounts, product=None):
        if product:
            for key, acc in accounts.items():
                ref_account = self.account_ids.search([
                    ('account_src_id', '=', acc.id),
                    '|', ('product_type', '=', product.type),
                    ('product_type', '=', False)
                ])
                if len(ref_account) > 1:
                    raise UserError(
                        _('There is more than one mapping in the '
                          'fiscal position for the same account.')
                    )
                if ref_account:
                    accounts[key] = ref_account.account_dest_id
            return accounts
        else:
            super(AccountFiscalPosition, self).map_accounts(accounts)

    @api.model
    def map_tax(self, taxes, product=None, partner=None):
        if product:
            result = self.env['account.tax'].browse()
            for tax in taxes:
                tax_count = 0
                for t in self.tax_ids:
                    if t.tax_src_id == tax and (
                                    t.product_type == product.type or
                                    t.product_type is False):
                        tax_count += 1
                        if t.tax_dest_id:
                            result |= t.tax_dest_id
                if not tax_count:
                    result |= tax
            return result
        else:
            return super(AccountFiscalPosition, self).\
                map_tax(taxes, product, partner)


class AccountFiscalPositionTax(models.Model):
    _inherit = 'account.fiscal.position.tax'

    product_type = fields.Selection([
        ('consu', 'Products'),
        ('service', 'Services')],
        string="Product Type",
        help='If the account is related to specific type of '
             'product, please add it here.'
             'If you leave the field empty, it will be used '
             'for both product types.'
    )


class AccountFiscalPositionAccount(models.Model):
    _inherit = 'account.fiscal.position.account'

    product_type = fields.Selection([
        ('consu', 'Products'),
        ('service', 'Services')],
        string="Product Type",
        help='If the tax is related to specific type of '
             'product, please add it here.'
             'If you leave the field empty, it will be used '
             'for both product types.'
    )
