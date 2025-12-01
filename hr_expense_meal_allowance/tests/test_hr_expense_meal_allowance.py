from datetime import datetime

from odoo.addons.base.tests.common import BaseCommon


class HrExpenseMealAllowance(BaseCommon):
    def setUp(self):
        super().setUp()
        # Create currency and company
        self.currency = self.env.ref("base.USD")
        self.company = self.env.ref("base.main_company")
        # Create user and employee
        self.user = self.env.ref("base.user_admin")
        self.employee = self.env.ref("hr.employee_admin")

        # Create city with rates
        self.rate_with_city_name = self.env["hr.expense.meal.allowance.rate"].create(
            {
                "city_name": "Test City",
                "country_id": self.env.ref("base.de").id,  # Assuming DE as the country
                "daily_rate_8h": 50,
                "daily_rate_24h": 100,
            }
        )

        # Create city with rates
        self.rate_without_city_name = self.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": self.env.ref("base.es").id,  # Assuming ES as the country
                "daily_rate_8h": 100,
                "daily_rate_24h": 200,
            }
        )

        # Create hr.expense
        self.travel_begin = datetime(2024, 6, 1, 8, 0, 0)
        self.travel_end = datetime(2024, 6, 1, 18, 30, 0)
        self.hr_expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "employee_id": self.employee.id,
                "travel_begin": datetime(2024, 6, 1, 8, 0, 0),
                "travel_end": datetime(2024, 6, 1, 18, 30, 0),
                "meal_allowance_rate_id": self.rate_with_city_name.id,
                "company_id": self.company.id,
            }
        )

    def test_compute_day_field(self):
        meal = self.env["hr.expense.meal.allowance"].create(
            {
                "date": "2024-06-01",
                "hr_expense_id": self.hr_expense.id,
            }
        )
        self.assertEqual(meal.day, "Saturday")
