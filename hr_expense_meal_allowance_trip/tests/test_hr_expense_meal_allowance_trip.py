# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import datetime

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


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

        cls.partner = cls.env["res.partner"].create({"name": "Trip Customer"})
        cls.trip_de = cls.env["hr.trip"].create(
            {
                "name": "German Trip",
                "start_date": datetime(2024, 6, 1, 8, 0),
                "end_date": datetime(2024, 6, 3, 18, 0),
                "employee_id": cls.employee_de.id,
                "partner_id": cls.partner.id,
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

    def _meal_allowance_product(self):
        return self.env.ref(
            "hr_expense_meal_allowance.product_meal_allowance"
        ).product_variant_id

    def _set_timezones(self):
        # Meal allowance day computation needs a timezone.
        self.employee_de.tz = "Europe/Berlin"
        self.env.user.tz = "Europe/Berlin"

    def test_selecting_trip_fills_empty_travel_info(self):
        self._set_timezones()
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self._meal_allowance_product()
            self.assertFalse(form.travel_begin)
            form.trip_id = self.trip_de
            self.assertEqual(form.travel_begin, self.trip_de.start_date)
            self.assertEqual(form.travel_end, self.trip_de.end_date)
            self.assertEqual(form.customer_id, self.partner)
            expense = form.save()
        self.assertEqual(expense.trip_id, self.trip_de)
        self.assertTrue(
            expense.meal_allowance_ids,
            "Day lines should be generated from the travel dates set by the trip.",
        )

    def test_selecting_trip_keeps_existing_travel_info(self):
        self._set_timezones()
        other_partner = self.env["res.partner"].create({"name": "Other Customer"})
        begin = datetime(2024, 6, 2, 9, 0)
        end = datetime(2024, 6, 2, 20, 0)
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self._meal_allowance_product()
            form.travel_begin = begin
            form.travel_end = end
            form.customer_id = other_partner
            form.trip_id = self.trip_de
            self.assertEqual(form.travel_begin, begin)
            self.assertEqual(form.travel_end, end)
            self.assertEqual(form.customer_id, other_partner)

    def test_selecting_trip_before_product_fills_travel_info(self):
        self._set_timezones()
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.trip_id = self.trip_de
            # Not a meal allowance yet: nothing is filled.
            self.assertFalse(form.travel_begin)
            form.product_id = self._meal_allowance_product()
            self.assertEqual(form.travel_begin, self.trip_de.start_date)
            self.assertEqual(form.travel_end, self.trip_de.end_date)
            self.assertEqual(form.customer_id, self.partner)

    def test_selecting_trip_on_regular_expense_does_nothing(self):
        product = self.env["product.product"].create(
            {"name": "Taxi", "can_be_expensed": True}
        )
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = product
            form.trip_id = self.trip_de
            self.assertFalse(form.travel_begin)
            self.assertFalse(form.travel_end)
            self.assertFalse(form.customer_id)

    def test_trip_field_context_prefills_new_trip(self):
        """Creating a trip from the expense form gets the expense's values."""
        arch = self.env["hr.expense"].get_view(view_type="form")["arch"]
        node = etree.fromstring(arch).xpath("//field[@name='trip_id']")[0]
        # Dates outside the existing trips, as trips must not overlap.
        begin = datetime(2024, 7, 1, 8, 0)
        end = datetime(2024, 7, 3, 18, 0)
        context = safe_eval(
            node.get("context"),
            {
                "employee_id": self.employee_de.id,
                "name": "Customer visit",
                "customer_id": self.partner.id,
                "travel_begin": begin,
                "travel_end": end,
            },
        )
        self.assertEqual(context.get("search_default_open_trips"), 1)
        # "Create and edit" opens the trip form with the context defaults.
        with Form(self.env["hr.trip"].with_context(**context)) as trip_form:
            trip = trip_form.save()
        self.assertEqual(trip.employee_id, self.employee_de)
        self.assertEqual(trip.name, "Customer visit")
        self.assertEqual(trip.partner_id, self.partner)
        self.assertEqual(trip.start_date, begin)
        self.assertEqual(trip.end_date, end)
