from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("post_install", "-at_install")
class TestHrExpenseSheet(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expense_employee.tz = "Europe/Berlin"
        cls.meal_allowance_product = cls.env.ref(
            "hr_expense_meal_allowance.product_meal_allowance"
        ).product_variant_id
        cls.rate = cls.env["hr.expense.meal.allowance.rate"].create(
            {
                "country_id": cls.env.ref("base.de").id,
                "city_name": "Berlin",
                "currency_id": cls.company_data["currency"].id,
                "daily_rate_8h": 50,
                "daily_rate_24h": 100,
            }
        )

    def _create_meal_allowance_sheet(self):
        sheet = self.create_expense_report(
            {
                "name": "Meal Allowance Report",
                "expense_line_ids": [
                    Command.create(
                        {
                            "name": "Business trip to Berlin",
                            "employee_id": self.expense_employee.id,
                            "product_id": self.meal_allowance_product.id,
                            "payment_mode": "own_account",
                            "company_id": self.company_data["company"].id,
                            "date": "2023-10-31",
                            "travel_begin": "2023-10-30 07:00:00",
                            "travel_end": "2023-10-31 17:00:00",
                            "meal_allowance_rate_id": self.rate.id,
                        }
                    )
                ],
            }
        )
        sheet.expense_line_ids._update_meal_lines()
        return sheet

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_create_moves_renders_meal_allowance_report(self, mock_render):
        """Approving a sheet renders the report for meal allowances without receipt."""
        mock_render.return_value = (b"PDF content", "pdf")
        sheet = self._create_meal_allowance_sheet()

        sheet.action_submit_sheet()
        sheet.action_approve_expense_sheets()

        mock_render.assert_called_once_with(
            "hr_expense_meal_allowance.action_report_hr_expense_meal_allowance",
            sheet.expense_line_ids.id,
            None,
        )

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_create_moves_skips_expense_with_attachment(self, mock_render):
        """No report is rendered when the employee already attached a receipt."""
        mock_render.return_value = (b"PDF content", "pdf")
        sheet = self._create_meal_allowance_sheet()
        self.env["ir.attachment"].create(
            {
                "name": "receipt.pdf",
                "res_model": "hr.expense",
                "res_id": sheet.expense_line_ids.id,
                "datas": b"",
            }
        )

        sheet.action_submit_sheet()
        sheet.action_approve_expense_sheets()

        mock_render.assert_not_called()

    @patch("odoo.addons.base.models.ir_actions_report.IrActionsReport._render_qweb_pdf")
    def test_create_moves_skips_regular_expense(self, mock_render):
        """No report is rendered for expenses that are not meal allowances."""
        mock_render.return_value = (b"PDF content", "pdf")
        sheet = self.create_expense_report({"name": "Regular Report"})

        sheet.action_submit_sheet()
        sheet.action_approve_expense_sheets()

        mock_render.assert_not_called()
