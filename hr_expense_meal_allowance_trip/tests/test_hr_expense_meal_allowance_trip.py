# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from datetime import date, datetime

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
        # Meal allowance day computation needs a timezone; the model falls back
        # to the employee's tz and then to the current user's tz.
        cls.employee_de.tz = "Europe/Berlin"
        cls.env.user.tz = "Europe/Berlin"

        cls.partner = cls.env["res.partner"].create({"name": "Trip Customer"})
        cls.other_partner = cls.env["res.partner"].create({"name": "Other Customer"})
        cls.trip_de = cls.env["hr.trip"].create(
            {
                "name": "German Trip",
                "start_date": datetime(2024, 6, 1, 8, 0),
                "end_date": datetime(2024, 6, 3, 18, 0),
                "employee_id": cls.employee_de.id,
                "partner_id": cls.partner.id,
            }
        )
        cls.trip_de_other = cls.env["hr.trip"].create(
            {
                "name": "Other German Trip",
                "start_date": datetime(2024, 6, 10, 9, 0),
                "end_date": datetime(2024, 6, 12, 17, 0),
                "employee_id": cls.employee_de.id,
                "partner_id": cls.other_partner.id,
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
        cls.meal_allowance_product = cls.env.ref(
            "hr_expense_meal_allowance.product_meal_allowance"
        ).product_variant_id
        cls.taxi_product = cls.env["product.product"].create(
            {"name": "Taxi", "can_be_expensed": True}
        )

    def _create_expense(self, product, **vals):
        return self.env["hr.expense"].create(
            {
                "name": vals.pop("name", product.name),
                "employee_id": self.employee_de.id,
                "product_id": product.id,
                "total_amount_currency": vals.pop("total_amount_currency", 10.0),
                **vals,
            }
        )

    def _create_meal_allowance(self, travel_begin, travel_end, **vals):
        vals.setdefault("date", travel_end.date() if travel_end else date(2024, 7, 15))
        return self._create_expense(
            self.meal_allowance_product,
            travel_begin=travel_begin,
            travel_end=travel_end,
            **vals,
        )

    # Availability of the button / action

    def test_available_for_german_company(self):
        self.assertTrue(self.trip_de.is_meal_allowance_available)

    def test_not_available_for_non_german_company(self):
        self.assertFalse(self.trip_us.is_meal_allowance_available)

    def test_recomputed_when_employee_changes(self):
        self.trip_us.employee_id = self.employee_de
        self.assertTrue(self.trip_us.is_meal_allowance_available)

    def test_not_available_for_done_trip(self):
        self.trip_de._set_state("done")
        self.assertFalse(self.trip_de.is_meal_allowance_available)
        with self.assertRaisesRegex(UserError, "cannot be created"):
            self.trip_de.action_create_meal_allowance()

    def test_available_when_trip_has_meal_allowance(self):
        """Several meal allowances per trip, e.g. per country or rate."""
        self._create_meal_allowance(
            self.trip_de.start_date, self.trip_de.end_date, trip_id=self.trip_de.id
        )
        self.assertTrue(self.trip_de.is_meal_allowance_available)
        action = self.trip_de.action_create_meal_allowance()
        self.assertEqual(action["context"]["default_trip_id"], self.trip_de.id)

    def test_action_raises_for_non_german_company(self):
        with self.assertRaisesRegex(UserError, "cannot be created"):
            self.trip_us.action_create_meal_allowance()

    def test_button_hidden_on_done_trip(self):
        arch = self.env["hr.trip"].get_view(view_type="form")["arch"]
        button = etree.fromstring(arch).xpath(
            "//button[@name='action_create_meal_allowance']"
        )[0]
        self.assertIn("is_meal_allowance_available", button.get("invisible"))
        self.assertIn("state == 'done'", button.get("invisible"))

    # Action and product lookup

    def test_action_returns_prefilled_expense(self):
        action = self.trip_de.action_create_meal_allowance()
        self.assertEqual(action["res_model"], "hr.expense")
        ctx = action["context"]
        self.assertEqual(ctx["default_trip_id"], self.trip_de.id)
        self.assertEqual(ctx["default_employee_id"], self.employee_de.id)
        self.assertEqual(ctx["default_product_id"], self.meal_allowance_product.id)
        self.assertEqual(ctx["default_travel_begin"], self.trip_de.start_date)
        self.assertEqual(ctx["default_travel_end"], self.trip_de.end_date)
        self.assertEqual(ctx["default_customer_id"], self.partner.id)

    def test_action_raises_when_product_missing(self):
        self.meal_allowance_product.action_archive()
        with self.assertRaisesRegex(UserError, "not configured"):
            self.trip_de.action_create_meal_allowance()

    def test_action_raises_when_tag_missing(self):
        self.env.ref("hr_expense_meal_allowance.product_tag_meal_allowance").unlink()
        with self.assertRaisesRegex(UserError, "not configured"):
            self.trip_de.action_create_meal_allowance()

    def test_product_lookup_respects_company_and_expensable(self):
        tag = self.env.ref("hr_expense_meal_allowance.product_tag_meal_allowance")
        self.meal_allowance_product.action_archive()
        # Not expensable, or belonging to another company: must not be picked.
        self.env["product.product"].create(
            {
                "name": "Not expensable",
                "can_be_expensed": False,
                "product_tag_ids": [(4, tag.id)],
            }
        )
        self.env["product.product"].create(
            {
                "name": "US only",
                "can_be_expensed": True,
                "company_id": self.company_us.id,
                "product_tag_ids": [(4, tag.id)],
            }
        )
        with self.assertRaisesRegex(UserError, "not configured"):
            self.trip_de.action_create_meal_allowance()
        own_product = self.env["product.product"].create(
            {
                "name": "German meal allowance",
                "can_be_expensed": True,
                "company_id": self.company_de.id,
                "product_tag_ids": [(4, tag.id)],
            }
        )
        action = self.trip_de.action_create_meal_allowance()
        self.assertEqual(action["context"]["default_product_id"], own_product.id)

    def test_created_expense_is_meal_allowance_linked_to_trip(self):
        action = self.trip_de.action_create_meal_allowance()
        expense_model = self.env["hr.expense"].with_context(**action["context"])
        with Form(expense_model) as form:
            expense = form.save()
        self.assertTrue(expense.is_meal_allowance)
        self.assertEqual(expense.trip_id, self.trip_de)
        self.assertEqual(expense.employee_id, self.employee_de)
        self.assertEqual(expense.customer_id, self.partner)
        self.assertTrue(
            expense.meal_allowance_ids,
            "Meal allowance day lines should be generated from the trip dates.",
        )

    # Expense form: trip selection

    def test_selecting_trip_fills_travel_info(self):
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self.meal_allowance_product
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

    def test_changing_trip_keeps_travel_info(self):
        """Values filled from the first trip are not replaced by another trip."""
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self.meal_allowance_product
            form.trip_id = self.trip_de
            form.trip_id = self.trip_de_other
            self.assertEqual(form.travel_begin, self.trip_de.start_date)
            self.assertEqual(form.travel_end, self.trip_de.end_date)
            self.assertEqual(form.customer_id, self.partner)

    def test_trip_date_change_keeps_meal_allowance_dates(self):
        action = self.trip_de.action_create_meal_allowance()
        with Form(self.env["hr.expense"].with_context(**action["context"])) as form:
            expense = form.save()
        self.trip_de.end_date = datetime(2024, 6, 4, 18, 0)
        self.assertEqual(expense.travel_begin, datetime(2024, 6, 1, 8, 0))
        self.assertEqual(expense.travel_end, datetime(2024, 6, 3, 18, 0))

    def test_selecting_trip_keeps_entered_travel_info(self):
        begin = datetime(2024, 6, 2, 9, 0)
        end = datetime(2024, 6, 2, 20, 0)
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self.meal_allowance_product
            form.travel_begin = begin
            form.travel_end = end
            form.customer_id = self.other_partner
            form.trip_id = self.trip_de
            self.assertEqual(form.travel_begin, begin)
            self.assertEqual(form.travel_end, end)
            self.assertEqual(form.customer_id, self.other_partner)

    def test_selecting_trip_before_product_fills_travel_info(self):
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.trip_id = self.trip_de
            # Not a meal allowance yet: nothing is filled.
            self.assertFalse(form.travel_begin)
            form.product_id = self.meal_allowance_product
            self.assertEqual(form.travel_begin, self.trip_de.start_date)
            self.assertEqual(form.travel_end, self.trip_de.end_date)
            self.assertEqual(form.customer_id, self.partner)

    def test_becoming_meal_allowance_fills_only_empty_travel_info(self):
        begin = datetime(2024, 6, 2, 9, 0)
        expense = self.env["hr.expense"].new(
            {
                "employee_id": self.employee_de.id,
                "product_id": self.meal_allowance_product.id,
                "trip_id": self.trip_de.id,
                "travel_begin": begin,
                "customer_id": self.other_partner.id,
            }
        )
        self.assertTrue(expense.is_meal_allowance)
        expense._onchange_trip_id_fill_travel_info()
        # Values entered before are kept, empty ones come from the trip.
        self.assertEqual(expense.travel_begin, begin)
        self.assertEqual(expense.travel_end, self.trip_de.end_date)
        self.assertEqual(expense.customer_id, self.other_partner)

    def test_selecting_trip_on_regular_expense_does_nothing(self):
        with Form(self.env["hr.expense"]) as form:
            form.employee_id = self.employee_de
            form.product_id = self.taxi_product
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

    # Create Trip action from selected expenses

    def test_create_trip_covers_all_meal_allowances(self):
        """The trip spans all selected meal allowances, whatever their order."""
        later = self._create_meal_allowance(
            datetime(2024, 7, 5, 8, 0), datetime(2024, 7, 6, 18, 0)
        )
        earlier = self._create_meal_allowance(
            datetime(2024, 7, 1, 8, 0),
            datetime(2024, 7, 2, 18, 0),
            customer_id=self.partner.id,
        )
        (later | earlier).action_create_trip()
        trip = later.trip_id
        self.assertTrue(trip)
        self.assertEqual(trip, earlier.trip_id)
        self.assertEqual(trip.start_date, datetime(2024, 7, 1, 8, 0))
        self.assertEqual(trip.end_date, datetime(2024, 7, 6, 18, 0))
        # The first customer that is actually set is used.
        self.assertEqual(trip.partner_id, self.partner)
        self.assertEqual(trip.employee_id, self.employee_de)

    def test_create_trip_ignores_empty_travel_dates(self):
        dated = self._create_meal_allowance(
            datetime(2024, 7, 1, 8, 0), datetime(2024, 7, 2, 18, 0)
        )
        undated = self._create_meal_allowance(False, False, date=date(2024, 7, 4))
        (dated | undated).action_create_trip()
        trip = dated.trip_id
        self.assertEqual(trip, undated.trip_id)
        self.assertEqual(trip.start_date, datetime(2024, 7, 1, 8, 0))
        # The undated meal allowance is still covered through its expense date.
        self.assertEqual(trip.end_date, datetime(2024, 7, 4, 0, 0))

    def test_create_trip_keeps_other_expenses_in_range(self):
        """Non meal allowance expenses extend the trip's date range as well."""
        taxi_before = self._create_expense(self.taxi_product, date=date(2024, 6, 30))
        meal = self._create_meal_allowance(
            datetime(2024, 7, 1, 8, 0), datetime(2024, 7, 3, 18, 0)
        )
        taxi_after = self._create_expense(self.taxi_product, date=date(2024, 7, 5))
        (taxi_before | meal | taxi_after).action_create_trip()
        trip = meal.trip_id
        self.assertEqual(trip, taxi_before.trip_id)
        self.assertEqual(trip, taxi_after.trip_id)
        self.assertEqual(trip.start_date, datetime(2024, 6, 30, 0, 0))
        self.assertEqual(trip.end_date, datetime(2024, 7, 5, 0, 0))

    def test_prepare_trip_create_vals_without_meal_allowance(self):
        taxi = self._create_expense(self.taxi_product, date=date(2024, 7, 5))
        vals = taxi._prepare_trip_create_vals(self.employee_de, taxi)
        self.assertEqual(vals["start_date"], date(2024, 7, 5))
        self.assertNotIn("partner_id", vals)
