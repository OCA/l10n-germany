# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import api, fields, models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    @api.onchange("trip_id", "is_meal_allowance")
    def _onchange_trip_id_fill_travel_info(self):
        """Prefill the travel information of a meal allowance from its trip.

        Only empty values are filled, so information entered before the trip
        was selected is never overwritten and the travel dates of a meal
        allowance stay independent of later changes of the trip.
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
        """Widen the trip with the travel information of the meal allowances.

        The date range of the parent covers the expense dates of all selected
        expenses; it is only extended by the travel dates of the meal
        allowances, so no selected expense ends up outside the trip. Empty
        travel dates are ignored.
        """
        res = super()._prepare_trip_create_vals(employee, expenses)
        meal_allowance_expenses = expenses.filtered("is_meal_allowance")
        if not meal_allowance_expenses:
            return res
        start_dates = [fields.Datetime.to_datetime(res.get("start_date"))]
        start_dates += meal_allowance_expenses.mapped("travel_begin")
        end_dates = [fields.Datetime.to_datetime(res.get("end_date"))]
        end_dates += meal_allowance_expenses.mapped("travel_end")
        start_dates = [date for date in start_dates if date]
        end_dates = [date for date in end_dates if date]
        if start_dates:
            res["start_date"] = min(start_dates)
        if end_dates:
            res["end_date"] = max(end_dates)
        # First customer that is actually set on one of the meal allowances
        customer = meal_allowance_expenses.customer_id[:1]
        if customer and not res.get("partner_id"):
            res["partner_id"] = customer.id
        if not res.get("name"):
            described = (
                meal_allowance_expenses.filtered("description")[:1]
                or meal_allowance_expenses[:1]
            )
            res["name"] = described.description or described.name or ""
        return res
