# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import datetime

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestHrExpenseMealAllowanceTrip(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.germany = cls.env.ref("base.de")
        cls.usa = cls.env.ref("base.us")

        # Use the acting user's own company as the German company so that
        # expenses can be created in-company (no multi-company inconsistency).
        cls.company_de = cls.env.company
        cls.company_de.country_id = cls.germany
        cls.company_us = cls.env["res.company"].create(
            {"name": "US Company", "country_id": cls.usa.id}
        )

        cls.employee_de = cls.env["hr.employee"].create(
            {"name": "German Employee", "company_id": cls.company_de.id}
        )
        cls.employee_us = cls.env["hr.employee"].create(
            {"name": "US Employee", "company_id": cls.company_us.id}
        )

        cls.trip_de = cls.env["hr.trip"].create(
            {
                "name": "German Trip",
                "start_date": datetime(2024, 6, 1, 8, 0),
                "end_date": datetime(2024, 6, 3, 18, 0),
                "employee_id": cls.employee_de.id,
            }
        )
        cls.trip_us = cls.env["hr.trip"].create(
            {
                "name": "US Trip",
                "start_date": datetime(2024, 6, 4, 8, 0),
                "end_date": datetime(2024, 6, 6, 18, 0),
                "employee_id": cls.employee_us.id,
            }
        )

    def test_available_for_german_company(self):
        self.assertTrue(self.trip_de.is_meal_allowance_available)

    def test_not_available_for_non_german_company(self):
        self.assertFalse(self.trip_us.is_meal_allowance_available)

    def test_recomputed_when_employee_changes(self):
        self.trip_us.employee_id = self.employee_de
        self.assertTrue(self.trip_us.is_meal_allowance_available)

    def test_action_returns_prefilled_expense(self):
        action = self.trip_de.action_create_meal_allowance()
        self.assertEqual(action["res_model"], "hr.expense")
        ctx = action["context"]
        product = self.env.ref(
            "hr_expense_meal_allowance.product_meal_allowance"
        ).product_variant_id
        self.assertEqual(ctx["default_trip_id"], self.trip_de.id)
        self.assertEqual(ctx["default_employee_id"], self.employee_de.id)
        self.assertEqual(ctx["default_product_id"], product.id)
        self.assertEqual(ctx["default_travel_begin"], self.trip_de.start_date)
        self.assertEqual(ctx["default_travel_end"], self.trip_de.end_date)

    def test_action_raises_for_non_german_company(self):
        with self.assertRaises(UserError):
            self.trip_us.action_create_meal_allowance()

    def test_created_expense_is_meal_allowance_linked_to_trip(self):
        # Meal allowance day computation needs a timezone; the model falls back
        # to the employee's tz and then to the current user's tz.
        self.employee_de.tz = "Europe/Berlin"
        self.env.user.tz = "Europe/Berlin"
        action = self.trip_de.action_create_meal_allowance()
        expense_model = self.env["hr.expense"].with_context(**action["context"])
        with Form(expense_model) as form:
            expense = form.save()
        self.assertTrue(expense.is_meal_allowance)
        self.assertEqual(expense.trip_id, self.trip_de)
        self.assertEqual(expense.employee_id, self.employee_de)
        self.assertTrue(
            expense.meal_allowance_ids,
            "Meal allowance day lines should be generated from the trip dates.",
        )
