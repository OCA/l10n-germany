# Copyright 2025 Maik Derstappen (https://derico.de)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_labor_cost_product = fields.Boolean(
        string="Is Labor Cost Product",
        help="Indicates whether this product is a labor product.",
    )

    @api.onchange("is_labor_cost_product", "type")
    def _check_labor_cost_product_type(self):
        for record in self:
            if record.is_labor_cost_product and record.type in ("consu", "combo"):
                raise ValidationError(
                    "Labor cost products cannot be of type 'Goods' or 'Combo'."
                )