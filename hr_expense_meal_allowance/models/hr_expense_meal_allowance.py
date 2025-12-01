from datetime import timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrExpenseMealAllowance(models.Model):
    _name = "hr.expense.meal.allowance"
    _description = "Expense Meal Allowances for a date."
    _order = "date"

    date = fields.Date(required=True)
    day = fields.Char(compute="_compute_date")
    breakfast_included = fields.Boolean(string="Breakfast included?")
    lunch_included = fields.Boolean(string="Lunch included?")
    dinner_included = fields.Boolean(string="Dinner included?")

    currency_id = fields.Many2one(
        "res.currency",
        related="hr_expense_id.currency_id",
        readonly=True,
        help="Utility field to express amount currency",
    )
    expense_for_day = fields.Monetary(
        string="Expenses for This Day",
        compute="_compute_expense_for_day",
        currency_field="currency_id",
    )
    hr_expense_id = fields.Many2one("hr.expense", string="Expense", readonly=True)

    employee_id = fields.Many2one(related="hr_expense_id.employee_id")
    is_editable = fields.Boolean(
        related="hr_expense_id.is_editable",
    )

    @api.depends("date")
    def _compute_date(self):
        for record in self:
            if record.date:
                record.day = self.env._(record.date.strftime("%A"))
            else:
                record.day = ""

    @api.depends(
        "date",
        "breakfast_included",
        "lunch_included",
        "dinner_included",
        "hr_expense_id.travel_end",
        "hr_expense_id.travel_begin",
        "hr_expense_id.meal_allowance_rate_id",
    )
    def _compute_expense_for_day(self):
        for record in self:
            # always use the timezone of the employee
            timezone = record.employee_id.user_id.tz or self.env.user.tz
            if not timezone:
                raise UserError(self.env._("Please set a timezone in user settings"))

            expense_for_day = 0
            if (
                record.date
                and record.hr_expense_id.travel_end
                and record.hr_expense_id.travel_begin
            ):
                tz = pytz.timezone(timezone)
                date_travel_begin = record.hr_expense_id.travel_begin.astimezone(
                    tz
                ).date()
                date_travel_end = record.hr_expense_id.travel_end.astimezone(tz).date()

                city = record.hr_expense_id.meal_allowance_rate_id
                if date_travel_begin == date_travel_end:
                    # one day trip
                    duration = (
                        record.hr_expense_id.travel_end
                        - record.hr_expense_id.travel_begin
                    )
                    if duration > timedelta(hours=8):
                        expense_for_day = city.daily_rate_8h

                elif record.date in [date_travel_begin, date_travel_end]:
                    # trip start or end day
                    expense_for_day = (
                        record.hr_expense_id.meal_allowance_rate_id.daily_rate_8h
                    )
                else:
                    expense_for_day = (
                        record.hr_expense_id.meal_allowance_rate_id.daily_rate_24h
                    )

                if record.breakfast_included:
                    expense_for_day -= city.breakfast_rate
                if record.lunch_included:
                    expense_for_day -= city.lunch_rate
                if record.dinner_included:
                    expense_for_day -= city.dinner_rate

            record.expense_for_day = max(expense_for_day, 0)
