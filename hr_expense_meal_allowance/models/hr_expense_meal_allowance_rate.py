from odoo import api, fields, models
from odoo.tools import format_date


class HrExpenseMealAllowanceRate(models.Model):
    _name = "hr.expense.meal.allowance.rate"
    _description = "Expense meal allowances rate for a city or country."

    city_name = fields.Char(translate=True)
    country_id = fields.Many2one("res.country", required=True)
    daily_rate_24h = fields.Monetary(string="Daily Rate - 24h")
    daily_rate_8h = fields.Monetary(string="Daily Rate - 8h")
    percentage_for_breakfast = fields.Float(
        string="Percentage for Breakfast", default=0.2
    )
    percentage_for_lunch = fields.Float(string="Percentage for Lunch", default=0.4)
    percentage_for_dinner = fields.Float(string="Percentage for Dinner", default=0.4)

    breakfast_rate = fields.Monetary(compute="_compute_expense_rate")
    lunch_rate = fields.Monetary(compute="_compute_expense_rate")
    dinner_rate = fields.Monetary(compute="_compute_expense_rate")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.ref("base.EUR").id,
    )
    expire_on = fields.Date()

    @api.model
    def _search_display_name(self, operator, value):
        if isinstance(value, str) and value:
            domain = [
                "|",
                ("country_id.name", operator, value),
                ("city_name", operator, value),
            ]
            return domain
        return super()._search_display_name(operator, value)

    @api.depends(
        "daily_rate_24h",
        "percentage_for_breakfast",
        "percentage_for_lunch",
        "percentage_for_dinner",
    )
    def _compute_expense_rate(self):
        for rate in self:
            rate.breakfast_rate = rate.daily_rate_24h * rate.percentage_for_breakfast
            rate.lunch_rate = rate.daily_rate_24h * rate.percentage_for_lunch
            rate.dinner_rate = rate.daily_rate_24h * rate.percentage_for_dinner

    @api.depends("city_name", "country_id")
    def _compute_display_name(self):
        for rate in self:
            display_name = ""
            if rate.city_name:
                display_name = f"{rate.country_id.name} - {rate.city_name}"
            else:
                display_name = rate.country_id.name

            if rate.expire_on:
                display_name += self.env._(
                    " (valid until %(expire_on)s)",
                    expire_on=format_date(self.env, rate.expire_on),
                )

            rate.display_name = display_name
