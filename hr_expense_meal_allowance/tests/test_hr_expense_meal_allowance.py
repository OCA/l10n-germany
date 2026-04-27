from datetime import datetime
from unittest.mock import PropertyMock, patch

from odoo.exceptions import UserError

from odoo.addons.base.tests.common import BaseCommon


class HrExpenseMealAllowance(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country = cls.env.ref("base.de")
        cls.rate = cls.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": cls.country.id,
                "city_name": "Berlin",
                "daily_rate_8h": 50.0,
                "daily_rate_24h": 100.0,
                "percentage_for_breakfast": 0.2,
                "percentage_for_lunch": 0.4,
                "percentage_for_dinner": 0.4,
            }
        )
        cls.employee = cls.env.ref("hr.employee_admin")
        cls.employee.user_id.tz = "Europe/Berlin"
        cls.expense = cls.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "employee_id": cls.employee.id,
                "travel_begin": datetime(2023, 10, 30, 8, 0, 0),
                "travel_end": datetime(2023, 11, 1, 18, 0, 0),
                "meal_allowance_rate_id": cls.rate.id,
                "company_id": cls.company.id,
            }
        )

    def _create_line(self, date):
        return self.env["hr.expense.meal.allowance"].create(
            {
                "date": date,
                "hr_expense_id": self.expense.id,
            }
        )

    def test_compute_date_with_value(self):
        line = self._create_line(datetime(2023, 10, 30).date())
        line._compute_date()
        self.assertTrue(line.day)

    def test_compute_date_empty(self):
        line = self.env["hr.expense.meal.allowance"].new(
            {
                "date": False,
            }
        )
        line._compute_date()
        self.assertEqual(line.day, "")

    def test_missing_timezone_raises(self):
        line = self.env["hr.expense.meal.allowance"].new(
            {
                "date": datetime(2023, 10, 30).date(),
                "hr_expense_id": self.expense.id,
            }
        )
        with patch.object(
            type(self.env.user), "tz", new_callable=PropertyMock, return_value=False
        ):
            with self.assertRaises(UserError):
                line._compute_expense_for_day()

    def test_one_day_trip_over_8h(self):
        self.expense.travel_begin = datetime(2023, 10, 30, 8, 0, 0)
        self.expense.travel_end = datetime(2023, 10, 30, 19, 0, 0)
        line = self._create_line(datetime(2023, 10, 30).date())
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 50.0)

    def test_start_or_end_day_uses_8h_rate(self):
        self.expense.travel_begin = datetime(2023, 10, 30, 8, 0, 0)
        self.expense.travel_end = datetime(2023, 11, 1, 18, 0, 0)
        line = self._create_line(datetime(2023, 10, 30).date())
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 50.0)

    def test_middle_day_uses_24h_rate(self):
        self.expense.travel_begin = datetime(2023, 10, 30, 8, 0, 0)
        self.expense.travel_end = datetime(2023, 11, 2, 18, 0, 0)
        line = self._create_line(datetime(2023, 11, 1).date())
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 100.0)

    def test_breakfast_deduction(self):
        line = self._create_line(datetime(2023, 10, 31).date())
        line.breakfast_included = True
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 100.0 - self.rate.breakfast_rate)

    def test_lunch_deduction(self):
        line = self._create_line(datetime(2023, 10, 31).date())
        line.lunch_included = True
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 100.0 - self.rate.lunch_rate)

    def test_dinner_deduction(self):
        line = self._create_line(datetime(2023, 10, 31).date())
        line.dinner_included = True
        line._compute_expense_for_day()
        self.assertEqual(line.expense_for_day, 100.0 - self.rate.dinner_rate)

    def test_expense_never_negative(self):
        line = self._create_line(datetime(2023, 10, 31).date())
        line.breakfast_included = True
        line.lunch_included = True
        line.dinner_included = True
        line._compute_expense_for_day()
        self.assertGreaterEqual(line.expense_for_day, 0)
