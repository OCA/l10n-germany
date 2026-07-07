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
