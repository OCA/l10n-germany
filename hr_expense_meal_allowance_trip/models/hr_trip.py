# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrTrip(models.Model):
    _inherit = "hr.trip"

    is_meal_allowance_available = fields.Boolean(
        string="Meal Allowance Available",
        compute="_compute_is_meal_allowance_available",
        help="Technical field: enabled when the trip's employee belongs to a "
        "German company, allowing the creation of meal allowances.",
    )

    @api.depends(
        "employee_id",
        "employee_id.company_id",
        "employee_id.company_id.country_id",
        "expense_ids",
        "expense_ids.product_id",
    )
    def _compute_is_meal_allowance_available(self):
        germany = self.env.ref("base.de", raise_if_not_found=False)
        for trip in self:
            company = trip.employee_id.company_id
            trip.is_meal_allowance_available = (
                bool(germany and company and company.country_id == germany)
                # all trip.expense_ids.product_id.is_meal_allowance is False
                and not any(trip.expense_ids.mapped("is_meal_allowance"))
            )

    def action_create_meal_allowance(self):
        self.ensure_one()
        if not self.is_meal_allowance_available:
            raise UserError(
                self.env._(
                    "Meal allowances can only be created for employees of a "
                    "German company."
                )
            )
        meal_allowance_tag = self.env.ref(
            "hr_expense_meal_allowance.product_tag_meal_allowance", False
        )
        product = self.env["product.product"].search(
            [("product_tmpl_id.product_tag_ids", "in", [meal_allowance_tag.id])],
            limit=1,
        )
        if not product:
            raise UserError(self.env._("The meal allowance product is not configured."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Meal Allowance"),
            "res_model": "hr.expense",
            "view_mode": "form",
            "views": [(self.env.ref("hr_expense.hr_expense_view_form").id, "form")],
            "target": "current",
            "context": {
                "default_employee_id": self.employee_id.id,
                "default_product_id": product.id,
                "default_trip_id": self.id,
                "default_travel_begin": self.start_date,
                "default_travel_end": self.end_date,
                "default_customer_id": self.partner_id.id,
            },
        }
