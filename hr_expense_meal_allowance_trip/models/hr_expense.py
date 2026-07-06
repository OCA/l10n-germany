# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def _prepare_trip_create_vals(self, employee, expenses):
        """Prepare values for creating a trip from selected expenses.
        This hook exists so downstream modules can override trip defaults.
        """
        res = super()._prepare_trip_create_vals(employee, expenses)
        meal_allowance_expenses = expenses.filtered(lambda e: e.is_meal_allowance)
        if meal_allowance_expenses:
            res["start_date"] = min(meal_allowance_expenses[0].mapped("travel_begin"))
            res["end_date"] = max(meal_allowance_expenses.mapped("travel_end"))
            res["partner_id"] = meal_allowance_expenses[0].customer_id.id
            if not res.get("name"):
                meal_allowance_description = (
                    meal_allowance_expenses.filtered(lambda e: e.description)
                    or meal_allowance_expenses
                )[0]
                res["name"] = (
                    meal_allowance_description.description
                    or meal_allowance_description.name
                    or ""
                )
        return res
