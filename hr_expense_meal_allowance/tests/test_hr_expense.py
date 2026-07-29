from datetime import datetime
from unittest.mock import patch

import pytz

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Command, Form

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
        cls.employee_tz = pytz.timezone(cls.employee.tz)

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
            f.travel_begin = (
                self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            f.travel_end = (
                self.employee_tz.localize(datetime(2023, 10, 31, 18, 0, 0))
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            f.customer_id = self.customer

        # assert
        self.assertEqual(f.meal_allowance_rate_id, self.rate)

    def test_update_meal_lines_end_midnight(self):
        """Test that meal lines are created correctly based on travel dates."""
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 1, 0, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 5, 12, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()

        self.assertEqual(expense.number_of_days, 4)
        self.assertEqual(expense.number_of_travel_days, 1)

    def test_update_meal_lines_start_midnight(self):
        """Test that meal lines are created correctly based on travel dates."""

        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 1, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 5, 0, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()

        self.assertEqual(expense.number_of_days, 3)
        self.assertEqual(expense.number_of_travel_days, 1)

    def test_update_meal_lines_full_day(self):
        """Test that meal lines are created correctly based on travel dates."""

        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 1, 0, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 2, 0, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()

        self.assertEqual(expense.number_of_days, 1)
        self.assertEqual(expense.number_of_travel_days, 0)

    def test_update_meal_lines(self):
        """Test that meal lines are created correctly based on travel dates."""
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": self.employee_tz.localize(
                    datetime(2023, 10, 30, 8, 0, 0)
                )
                .astimezone(pytz.utc)
                .replace(tzinfo=None),
                "travel_end": self.employee_tz.localize(datetime(2023, 11, 1, 18, 0, 0))
                .astimezone(pytz.utc)
                .replace(tzinfo=None),
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

        self.assertEqual(expense.number_of_days, 1)
        self.assertEqual(expense.number_of_travel_days, 2)

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
                "travel_begin": self.employee_tz.localize(
                    datetime(2023, 10, 30, 8, 0, 0)
                )
                .astimezone(pytz.utc)
                .replace(tzinfo=None),
                "travel_end": self.employee_tz.localize(
                    datetime(2023, 10, 30, 16, 0, 0)
                )
                .astimezone(pytz.utc)
                .replace(tzinfo=None),
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
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 16, 1, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        # act
        expense._update_meal_lines()
        # assert
        self.assertEqual(expense.total_amount_currency, 50)

    def test_travel_end_must_be_after_travel_begin(self):
        start = (
            self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )
        with self.assertRaises(ValidationError):
            self.env["hr.expense"].create(
                {
                    "name": "Invalid Trip",
                    "product_id": self.product.id,
                    "employee_id": self.employee.id,
                    "meal_allowance_rate_id": self.rate.id,
                    "company_id": self.company.id,
                    "travel_begin": start,
                    "travel_end": start,
                }
            )

    def test_total_amount_currency_recomputed_after_meal_change(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 11, 1, 18, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()
        initial_amount = expense.total_amount_currency

        expense.meal_allowance_ids[0].breakfast_included = True
        self.assertLess(expense.total_amount_currency, initial_amount)

    def test_number_of_travel_days_single_line(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Test",
                "employee_id": self.employee.id,
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 20, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
            }
        )
        expense.meal_allowance_ids = [
            Command.create({"date": datetime(2023, 10, 30).date()})
        ]
        expense._compute_number_of_travel_days()
        self.assertEqual(expense.number_of_days, 0)
        self.assertEqual(expense.number_of_travel_days, 1)

    def test_number_of_travel_days_zero_duration_midnight(self):
        start = (
            self.employee_tz.localize(datetime(2023, 10, 30, 0, 0, 0))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )

        with self.assertRaises(ValidationError):
            self.env["hr.expense"].create(
                {
                    "name": "Zero Duration",
                    "product_id": self.product.id,
                    "employee_id": self.employee.id,
                    "meal_allowance_rate_id": self.rate.id,
                    "company_id": self.company.id,
                    "travel_begin": start,
                    "travel_end": start,
                }
            )

    def test_update_meal_lines_sets_expense_date(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Test",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 11, 1, 18, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()
        self.assertEqual(expense.date, datetime(2023, 11, 1).date())

    def test_update_meal_lines_removes_old_lines(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Test Expense",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 11, 1, 18, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense._update_meal_lines()
        self.assertEqual(len(expense.meal_allowance_ids), 3)
        expense.travel_end = (
            self.employee_tz.localize(datetime(2023, 10, 31, 18, 0, 0))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )
        expense._update_meal_lines()
        self.assertEqual(len(expense.meal_allowance_ids), 2)

    def test_onchange_rate_fallback_country_only(self):
        customer = self.env["res.partner"].create(
            {
                "name": "No City Customer",
                "country_id": self.country.id,
            }
        )
        with Form(self.env["hr.expense"]) as f:
            f.product_id = self.product
            f.employee_id = self.employee
            f.travel_begin = (
                self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            f.travel_end = (
                self.employee_tz.localize(datetime(2023, 10, 31, 18, 0, 0))
                .astimezone(pytz.utc)
                .replace(tzinfo=None)
            )
            f.customer_id = customer

        self.assertTrue(f.meal_allowance_rate_id)

    def _create_meal_expense(self, name="Test"):
        expense = self.env["hr.expense"].create(
            {
                "name": name,
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 20, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
            }
        )
        expense._update_meal_lines()
        expense.flush_model()
        expense.is_meal_allowance = True
        return expense

    def _get_expense_attachments(self, expense):
        return (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "hr.expense"),
                    ("res_id", "=", expense.id),
                ]
            )
        )

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_do_approve_generates_report(self, mock_render):
        mock_render.return_value = (b"PDF content", "application/pdf")
        expense = self._create_meal_expense()
        expense.action_submit()
        expense.action_approve()
        expense.action_post()
        # Count only renders of the meal allowance report: other installed
        # modules may render additional reports (e.g. the vendor bill PDF)
        # during posting, which must not fail this test.
        meal_report_calls = [
            call
            for call in mock_render.call_args_list
            if "hr_expense_meal_allowance.action_report_hr_expense_meal_allowance"
            in call.args
        ]
        self.assertEqual(len(meal_report_calls), 1)
        attachments = self._get_expense_attachments(expense)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments.name, "Test.pdf")

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_do_approve_twice_single_pdf(self, mock_render):
        mock_render.return_value = (b"PDF content", "application/pdf")
        expense = self._create_meal_expense()
        # Read nb_attachment before any attachment exists: the compute has no
        # depends, so the zero stays in the transaction cache. The dedup must
        # not rely on it, or a second generation in the same transaction (e.g.
        # approval chained with posting) attaches a duplicate PDF.
        self.assertEqual(expense.nb_attachment, 0)
        expense.action_submit()
        if expense.state != "approved":
            expense.action_approve()
        expense._generate_expense_pdf_attachment()
        self.assertEqual(len(self._get_expense_attachments(expense)), 1)

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_do_approve_generates_report_with_receipt(self, mock_render):
        mock_render.return_value = (b"PDF content", "application/pdf")
        expense = self._create_meal_expense()
        receipt = self.env["ir.attachment"].create(
            {
                "name": "receipt.png",
                "raw": b"receipt",
                "res_model": "hr.expense",
                "res_id": expense.id,
                "mimetype": "image/png",
            }
        )
        expense.action_submit()
        if expense.state != "approved":
            expense.action_approve()
        attachments = self._get_expense_attachments(expense)
        self.assertEqual(len(attachments), 2)
        self.assertIn("Test.pdf", attachments.mapped("name"))
        self.assertIn(receipt, attachments)

    def test_update_meal_lines_missing_timezone(self):
        expense = self.env["hr.expense"].create(
            {
                "name": "Test",
                "product_id": self.product.id,
                "employee_id": self.employee.id,
                "travel_begin": (
                    self.employee_tz.localize(datetime(2023, 10, 30, 8, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "travel_end": (
                    self.employee_tz.localize(datetime(2023, 10, 31, 18, 0, 0))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                ),
                "meal_allowance_rate_id": self.rate.id,
                "company_id": self.company.id,
            }
        )
        expense.is_meal_allowance = True
        with (
            patch.object(
                type(expense.employee_id.user_id), "tz", new_callable=lambda: False
            ),
            patch.object(type(self.env.user), "tz", new_callable=lambda: False),
        ):
            with self.assertRaises(UserError):
                expense._update_meal_lines()
