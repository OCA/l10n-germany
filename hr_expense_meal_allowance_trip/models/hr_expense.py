# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.onchange("trip_id", "is_meal_allowance")
    def _onchange_trip_id_fill_travel_info(self):
        """Prefill the travel information of a meal allowance from its trip.

        Only empty values are filled, so information entered before the trip
        was selected is never overwritten.
        """
        for expense in self:
            trip = expense.trip_id
            if not trip or not expense.is_meal_allowance:
                continue
            if not expense.employee_id:
                expense.employee_id = trip.employee_id
            if not expense.travel_begin:
                expense.travel_begin = trip.start_date
            if not expense.travel_end:
                expense.travel_end = trip.end_date
            if not expense.customer_id:
                expense.customer_id = trip.partner_id

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
