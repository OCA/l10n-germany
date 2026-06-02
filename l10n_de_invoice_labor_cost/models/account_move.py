# Copyright 2025 Maik Derstappen (https://derico.de)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_de_labor_cost_untaxed = fields.Monetary(
        string="Labor Cost (Net)",
        compute="_compute_labor_cost_values",
        help="Total net amount of labor cost lines",
        store=True,
    )
    l10n_de_labor_cost_tax = fields.Monetary(
        string="Labor Cost (Tax)",
        compute="_compute_labor_cost_values",
        help="Total tax amount on labor cost lines",
        store=True,
    )
    l10n_de_labor_cost_total = fields.Monetary(
        string="Labor Cost (Gross)",
        compute="_compute_labor_cost_values",
        help="Total gross amount of labor cost lines (net + tax)",
        store=True,
    )

    @api.depends(
        "invoice_line_ids.tax_ids",
        "invoice_line_ids.price_subtotal",
        "invoice_line_ids.price_total",
        "move_type",
    )
    def _compute_labor_cost_values(self):
        for move in self:
            if move.move_type not in ["out_invoice", "out_refund"]:
                move.l10n_de_labor_cost_tax = 0
                move.l10n_de_labor_cost_untaxed = 0
                move.l10n_de_labor_cost_total = 0
                continue
            cost_untaxed = 0
            cost_total = 0
            for line in move.invoice_line_ids:
                if not line.product_id.is_labor_cost_product:
                    continue
                cost_untaxed += line.price_subtotal
                cost_total += line.price_total
            move.l10n_de_labor_cost_untaxed = cost_untaxed
            move.l10n_de_labor_cost_total = cost_total
            move.l10n_de_labor_cost_tax = cost_total - cost_untaxed
