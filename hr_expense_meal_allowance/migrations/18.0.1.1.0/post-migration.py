from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    rates = env["hr.expense.meal.allowance.rate"].search([])
    for rate in rates:
        rate.percentage_for_breakfast /= 100
        rate.percentage_for_lunch /= 100
        rate.percentage_for_dinner /= 100
