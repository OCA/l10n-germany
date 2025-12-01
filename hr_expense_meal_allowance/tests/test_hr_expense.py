from datetime import datetime

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class HrExpense(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
