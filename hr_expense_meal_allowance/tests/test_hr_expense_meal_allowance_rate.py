from datetime import date
from unittest.mock import patch

from odoo.addons.base.tests.common import BaseCommon


class HrExpenseMealAllowance(BaseCommon):
    def setUp(self):
        super().setUp()
        self.country = self.env["res.country"].search([], limit=1)
        self.city = self.env["hr.expense.meal.allowance.rate"].create(
            {
                "city_name": "Test City",
                "country_id": self.country.id,
                "daily_rate_24h": 100.0,
                "daily_rate_8h": 50.0,
                "percentage_for_breakfast": 0.3,
                "percentage_for_lunch": 0.5,
                "percentage_for_dinner": 0.2,
            }
        )

    def test_breakfast_rate(self):
        self.assertAlmostEqual(self.city.breakfast_rate, 30.0)

    def test_lunch_rate(self):
        self.assertAlmostEqual(self.city.lunch_rate, 50.0)

    def test_dinner_rate(self):
        self.assertAlmostEqual(self.city.dinner_rate, 20.0)

    def test_update_expense_rate_with_zero_percentages(self):
        self.city.percentage_for_breakfast = 0
        self.city.percentage_for_lunch = 0
        self.city.percentage_for_dinner = 0
        self.assertEqual(self.city.breakfast_rate, 0.0)
        self.assertEqual(self.city.lunch_rate, 0.0)
        self.assertEqual(self.city.dinner_rate, 0.0)

    def test_update_expense_rate_with_different_daily_rate(self):
        self.city.daily_rate_24h = 200.0
        self.assertAlmostEqual(self.city.breakfast_rate, 60.0)
        self.assertAlmostEqual(self.city.lunch_rate, 100.0)
        self.assertAlmostEqual(self.city.dinner_rate, 40.0)

    def test_search_display_name_city(self):
        domain = self.env["hr.expense.meal.allowance.rate"]._search_display_name(
            "ilike", "Test"
        )
        self.assertEqual(
            domain,
            [
                "|",
                ("country_id.name", "ilike", "Test"),
                ("city_name", "ilike", "Test"),
            ],
        )

    def test_display_name_with_city(self):
        self.assertEqual(
            self.city.display_name,
            f"{self.country.name} - Test City",
        )

    def test_display_name_without_city(self):
        rate = self.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": self.country.id,
                "daily_rate_24h": 100.0,
            }
        )

        self.assertEqual(
            rate.display_name,
            self.country.name,
        )

    def test_search_display_name_fallback(self):
        model = self.env["hr.expense.meal.allowance.rate"]

        with patch(
            "odoo.models.BaseModel._search_display_name",
            return_value=[("id", "=", 1)],
        ):
            result = model._search_display_name("=", False)

        self.assertEqual(result, [("id", "=", 1)])

    def test_display_name_with_expire_on(self):
        rate = self.env["hr.expense.meal.allowance.rate"].create(
            {
                "city_name": "Test City",
                "country_id": self.country.id,
                "daily_rate_24h": 100.0,
                "expire_on": date(2030, 1, 1),
            }
        )

        self.assertIn("valid until", rate.display_name)
