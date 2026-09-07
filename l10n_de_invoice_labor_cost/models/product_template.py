# Copyright 2025 Maik Derstappen (https://derico.de)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_labor_cost_product = fields.Boolean(
        help="Indicates whether this product is a labor product.",
    )

    def _check_is_labor_cost_product(self):
        self.ensure_one()
        if self.is_labor_cost_product and self.type in ("consu", "combo"):
            raise ValidationError(
                _("Labor cost products cannot be of type 'Goods' or 'Combo'.")
            )

    @api.constrains("is_labor_cost_product", "type")
    def _check_labor_cost_product_type(self):
        for record in self:
            record._check_is_labor_cost_product()

    @api.onchange("is_labor_cost_product", "type")
    def _onchange_check_labor_cost_product_type(self):
        self._check_labor_cost_product_type()
