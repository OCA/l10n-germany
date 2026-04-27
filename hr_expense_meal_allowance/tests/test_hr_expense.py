from datetime import datetime

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class HrExpense(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.tz = "Europe/Berlin"
        cls.country = cls.env.ref("base.de")
        cls.product = cls.env.ref(
            "hr_expense_meal_allowance.product_meal_allowance"
        ).product_variant_id
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Test Customer",
                "city": "Berlin",
                "country_id": cls.country.id,
            }
        )

        cls.employee = cls.env.ref("hr.employee_admin")

        cls.rate = cls.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": cls.country.id,
                "city_name": "Berlin",
                "currency_id": cls.env.ref("base.EUR").id,
                "expire_on": datetime(2023, 12, 31).date(),
                "daily_rate_8h": 50,
                "daily_rate_24h": 100,
                "percentage_for_breakfast": 0.2,
                "percentage_for_lunch": 0.4,
                "percentage_for_dinner": 0.4,
            }
        )
        cls.rate_before = cls.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": cls.country.id,
                "city_name": "Berlin",
                "currency_id": cls.env.ref("base.EUR").id,
                "expire_on": datetime(2022, 12, 31).date(),
            }
        )
        cls.rate_next = cls.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": cls.country.id,
                "city_name": "Berlin",
                "currency_id": cls.env.ref("base.EUR").id,
                "expire_on": False,
            }
        )

    def test_rate_display_name(self):
        """Test that meal allowance rate display name is correct."""
        # assert
        self.assertEqual(
            self.rate.display_name, "Germany - Berlin (valid until 12/31/2023)"
        )
        self.assertEqual(
            self.rate_before.display_name, "Germany - Berlin (valid until 12/31/2022)"
        )
        self.assertEqual(self.rate_next.display_name, "Germany - Berlin")

    def test_onchange_customer_with_city_and_country(self):
        """Test that meal allowance rate is set to correct year."""

        # act
        with Form(self.env["hr.expense"]) as f:
            f.product_id = self.product
            f.employee_id = self.employee
            f.travel_begin = datetime(2023, 10, 30, 8, 0, 0)
            f.travel_end = datetime(2023, 10, 31, 18, 0, 0)
            f.customer_id = self.customer

        # assert
        self.assertEqual(f.meal_allowance_rate_id, self.rate)

    def test_update_meal_lines(self):
        """Test that meal lines are created correctly based on travel dates."""
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": datetime(2023, 10, 30, 8, 0, 0),
                "travel_end": datetime(2023, 11, 1, 18, 0, 0),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        # act
        expense._update_meal_lines()

        # assert
        meal_lines = expense.meal_allowance_ids
        self.assertEqual(len(meal_lines), 3)
        self.assertEqual(meal_lines[0].date, datetime(2023, 10, 30).date())
        self.assertEqual(meal_lines[1].date, datetime(2023, 10, 31).date())
        self.assertEqual(meal_lines[2].date, datetime(2023, 11, 1).date())

        self.assertEqual(meal_lines[0].expense_for_day, 50)
        self.assertEqual(meal_lines[1].expense_for_day, 100)
        self.assertEqual(meal_lines[2].expense_for_day, 50)

        # act
        meal_lines[0].breakfast_included = True
        meal_lines[1].lunch_included = True
        meal_lines[2].lunch_included = True

        # assert
        self.assertEqual(meal_lines[0].expense_for_day, 30)
        self.assertEqual(meal_lines[1].expense_for_day, 60)
        self.assertEqual(meal_lines[2].expense_for_day, 10)

    def test_total_amount_currency_less_8h(self):
        """Test that meal lines are created correctly based on travel dates."""
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": datetime(2023, 10, 30, 8, 0, 0),
                "travel_end": datetime(2023, 10, 30, 16, 0, 0),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        # act
        expense._update_meal_lines()
        # assert
        self.assertEqual(expense.total_amount_currency, 0)

    def test_total_amount_currency_more_8h(self):
        """Test that meal lines are created correctly based on travel dates."""
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": datetime(2023, 10, 30, 8, 0, 0),
                "travel_end": datetime(2023, 10, 30, 16, 1, 0),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        # act
        expense._update_meal_lines()
        # assert
        self.assertEqual(expense.total_amount_currency, 50)
