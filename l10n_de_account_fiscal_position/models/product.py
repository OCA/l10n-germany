# Copyright 2019 Nikolina Todorova <nikolina.todorova@initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def get_product_accounts(self, fiscal_pos=None):
        accounts = self._get_product_accounts()
        if not fiscal_pos:
            fiscal_pos = self.env['account.fiscal.position']
        return fiscal_pos.map_accounts(accounts, self)
