# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class HrTrip(models.Model):
    _inherit = "hr.trip"

    is_meal_allowance_available = fields.Boolean(
        string="Meal Allowance Available",
        compute="_compute_is_meal_allowance_available",
        help="Technical field: enabled when a meal allowance can be created for "
        "the trip, i.e. the trip's employee belongs to a German company and "
        "the trip is not done yet.",
    )

    @api.depends("employee_id.company_id.country_id", "state")
    def _compute_is_meal_allowance_available(self):
        germany = self.env.ref("base.de", raise_if_not_found=False)
        for trip in self:
            company = trip.employee_id.company_id
            trip.is_meal_allowance_available = bool(
                germany
                and company
                and company.country_id == germany
                and trip.state != "done"
            )

    def _get_meal_allowance_product(self):
        """Return the meal allowance product to use for the trip.

        The product must carry the meal allowance tag, be expensable and be
        available in the company of the trip's employee.
        """
        self.ensure_one()
        product_model = self.env["product.product"]
        meal_allowance_tag = self.env.ref(
            "hr_expense_meal_allowance.product_tag_meal_allowance",
            raise_if_not_found=False,
        )
        if not meal_allowance_tag:
            return product_model
        company = self.employee_id.company_id or self.env.company
        return product_model.with_company(company).search(
            [
                ("product_tmpl_id.product_tag_ids", "in", meal_allowance_tag.ids),
                ("can_be_expensed", "=", True),
                ("company_id", "in", [False, company.id]),
            ],
            order="id",
            limit=1,
        )

    def action_create_meal_allowance(self):
        self.ensure_one()
        # The button is hidden whenever this is False; the check only guards
        # against direct calls.
        if not self.is_meal_allowance_available:
            raise UserError(
                self.env._(
                    "A meal allowance cannot be created for trip '%(trip)s'.",
                    trip=self.display_name,
                )
            )
        product = self._get_meal_allowance_product()
        if not product:
            raise UserError(self.env._("The meal allowance product is not configured."))
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Meal Allowance"),
            "res_model": "hr.expense",
            "view_mode": "form",
            "views": [(self.env.ref("hr_expense.hr_expense_view_form").id, "form")],
            "target": "current",
            "context": {
                "default_employee_id": self.employee_id.id,
                "default_product_id": product.id,
                "default_trip_id": self.id,
                "default_travel_begin": self.start_date,
                "default_travel_end": self.end_date,
                "default_customer_id": self.partner_id.id,
            },
        }
