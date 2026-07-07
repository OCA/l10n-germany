from odoo import models


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    def _do_create_moves(self):
        for sheet in self:
            for expense in sheet.expense_line_ids.filtered(
                lambda expense: expense.is_meal_allowance
                and not expense.message_attachment_count
            ):
                lang = self.employee_id.company_id.partner_id.lang
                self.env["ir.actions.report"].with_context(lang=lang)._render_qweb_pdf(
                    "hr_expense_meal_allowance.action_report_hr_expense_meal_allowance",
                    expense.id,
                )
        return super()._do_create_moves()
