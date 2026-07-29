from datetime import date, time, timedelta

from odoo import Command, api, fields, models
from odoo.exceptions import UserError, ValidationError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    travel_begin = fields.Datetime()
    travel_end = fields.Datetime()
    customer_id = fields.Many2one("res.partner")
    meal_allowance_rate_id = fields.Many2one(
        "hr.expense.meal.allowance.rate",
        string="Rate",
        domain="['|', ('expire_on', '=', False),('expire_on', '>=', travel_end)]",
    )

    number_of_days = fields.Integer(
        "Whole Days", compute="_compute_number_of_travel_days"
    )
    number_of_travel_days = fields.Integer(
        "Travel Days", compute="_compute_number_of_travel_days"
    )
    meal_allowance_ids = fields.One2many(
        "hr.expense.meal.allowance", "hr_expense_id", string="Included Meals"
    )
    is_meal_allowance = fields.Boolean(compute="_compute_meal_allowance_tag")

    @api.onchange("product_id")
    def _compute_meal_allowance_tag(self):
        meal_allowance_tag = self.env.ref(
            "hr_expense_meal_allowance.product_tag_meal_allowance", False
        )
        for record in self:
            record.is_meal_allowance = record.meal_allowance_ids or (
                meal_allowance_tag
                and meal_allowance_tag in record.product_id.product_tag_ids
            )

    @api.constrains("travel_begin", "travel_end")
    def _check_travel_dates(self):
        for record in self:
            if (
                record.travel_begin
                and record.travel_end
                and record.travel_end <= record.travel_begin
            ):
                raise ValidationError(
                    self.env._("Travel end must be later than travel begin.")
                )

    def _get_number_of_days(self):
        self.ensure_one()
        if not self.travel_begin or not self.travel_end:
            return 0, 0
        timezone = self.employee_id.tz or self.env.user.tz
        if not timezone:
            raise UserError(self.env._("Please set a timezone in user settings"))
        local_start = fields.Datetime.context_timestamp(
            self.with_context(tz=timezone), self.travel_begin
        )
        local_end = fields.Datetime.context_timestamp(
            self.with_context(tz=timezone), self.travel_end
        )
        if local_end < local_start:
            return 0, 0

        start_date = local_start.date()
        end_date = local_end.date()
        if local_end.time() == time(0) and end_date > start_date:
            end_date -= timedelta(days=1)

        if end_date < start_date:
            return 0, 0

        if start_date == end_date:
            if local_start.time() == time(0) and local_end.time() == time(0):
                return 1, 0
            return 0, 1

        span_days = (end_date - start_date).days + 1
        travel_days = 1 if local_start.time() != time(0) else 0
        if local_end.time() != time(0):
            travel_days += 1
        full_days = max(span_days - travel_days, 0)
        return full_days, travel_days

    @api.depends("travel_begin", "travel_end")
    def _compute_number_of_travel_days(self):
        for record in self:
            full_days, travel_days = record._get_number_of_days()
            record.number_of_days = full_days
            record.number_of_travel_days = travel_days

    @api.depends("is_meal_allowance", "meal_allowance_rate_id")
    def _compute_currency_id(self):
        res = super()._compute_currency_id()
        for expense in self:
            if expense.is_meal_allowance and expense.state in {"draft", "submitted"}:
                expense.currency_id = (
                    expense.meal_allowance_rate_id.currency_id
                    or expense.company_currency_id
                )
        return res

    @api.onchange("travel_begin", "travel_end", "customer_id")
    def _update_meal_lines(self):
        for record in self:
            if (
                not record.travel_begin
                or not record.travel_end
                or not record.is_meal_allowance
            ):
                record.meal_allowance_ids.unlink()
                continue

            if record.travel_end:
                record.date = record.travel_end.date()

            if record.is_meal_allowance:
                # always use the timezone of the employee
                timezone = record.employee_id.tz or self.env.user.tz
                if not timezone:
                    raise UserError(
                        self.env._("Please set a timezone in user settings")
                    )

                # create a line for each day in the timezone of the employee
                # if the end date is at 00:00, the last day does not count
                full_days, travel_days = record._get_number_of_days()
                local_start_date = fields.Datetime.context_timestamp(
                    record.with_context(tz=timezone), record.travel_begin
                ).date()
                date_range = [
                    local_start_date + timedelta(n)
                    for n in range(full_days + travel_days)
                ]

                # Map existing lines by date
                existing_lines_by_date = {
                    line.date: line for line in record.meal_allowance_ids
                }

                # Prepare new lines, preserving values for overlapping dates
                new_entries = []
                for date_ds in date_range:
                    existing_line = existing_lines_by_date.get(date_ds)
                    if existing_line:
                        new_entries.append(Command.link(existing_line.id))
                    else:
                        new_entries.append(
                            Command.create(
                                {
                                    "date": date_ds,
                                    "hr_expense_id": record.id,
                                }
                            )
                        )

                # Remove all old lines and recreate
                for unlink in record.meal_allowance_ids.filtered(
                    lambda allowance, date_range=date_range: allowance.date
                    not in date_range
                ):
                    new_entries.append(Command.unlink(unlink.id))
                record.meal_allowance_ids = new_entries

    @api.depends(
        "meal_allowance_ids",
        "meal_allowance_ids.expense_for_day",
        "meal_allowance_rate_id",
    )
    def _compute_total_amount_currency(self):
        res = super(
            HrExpense, self.filtered(lambda x: not x.is_meal_allowance)
        )._compute_total_amount_currency()

        for expense in self.filtered(lambda x: x.is_meal_allowance):
            price = sum(map(lambda x: x.expense_for_day, expense.meal_allowance_ids))
            expense.total_amount_currency = price
            if expense.meal_allowance_rate_id.currency_id:
                expense.currency_id = expense.meal_allowance_rate_id.currency_id
            expense._inverse_total_amount_currency()

        return res

    @api.onchange("customer_id", "travel_end")
    def _onchange_recalculate_meal_allowance_rate_id(self):
        for record in self:
            rates = []

            if (
                record.customer_id.city
                and record.customer_id.country_id
                and record.travel_end
            ):
                rates = self.env["hr.expense.meal.allowance.rate"].search(
                    [
                        ("country_id", "=", record.customer_id.country_id.id),
                        ("city_name", "=", record.customer_id.city),
                        "|",
                        ("expire_on", "=", False),
                        ("expire_on", ">=", record.travel_end.date()),
                    ],
                )

            if not rates and record.customer_id.country_id and record.travel_end:
                rates = self.env["hr.expense.meal.allowance.rate"].search(
                    [
                        ("country_id", "=", record.customer_id.country_id.id),
                        ("city_name", "=", ""),
                        "|",
                        ("expire_on", "=", False),
                        ("expire_on", ">=", record.travel_end.date()),
                    ],
                )
            rates = sorted(
                rates,
                key=lambda r: (r.expire_on is None, r.expire_on or date.max),
            )

            record.meal_allowance_rate_id = rates[0] if rates else False

    def _do_approve(self, check=True):
        """Override to auto-generate the meal allowance PDF on approval."""
        expenses_to_process = self.filtered(lambda e: e.state in ("submitted", "draft"))
        res = super()._do_approve(check=check)
        expenses_to_process.filtered(
            lambda e: e.state == "approved"
        )._generate_expense_pdf_attachment()

        return res

    def _generate_expense_pdf_attachment(self):
        """Render the meal allowance report as PDF and attach it once per expense."""
        # sudo is required: core forbids adding attachments to an approved
        # expense, and this runs post-approval. The existence check must also
        # run as sudo so it sees the previously generated attachment
        # regardless of the current user's access to it. It must be a real
        # search (not nb_attachment, whose compute has no depends and stays
        # stale for the whole transaction) so a second invocation in the same
        # transaction cannot create a duplicate.
        attachment_model = self.env["ir.attachment"].sudo()
        for expense in self.filtered("is_meal_allowance"):
            attachment_name = f"{expense.name}.pdf".replace("/", "_")
            if attachment_model.search_count(
                [
                    ("res_model", "=", "hr.expense"),
                    ("res_id", "=", expense.id),
                    ("name", "=", attachment_name),
                ],
                limit=1,
            ):
                continue
            # report_pdf_no_attachment: if the report action has a
            # "Save as Attachment Prefix" configured (e.g. set on the record
            # in the database), _render_qweb_pdf would itself create an
            # attachment during the render, duplicating the one created
            # below. Suppress that; this method is the only writer.
            pdf_content, _mime = (
                self.env["ir.actions.report"]
                .sudo()
                .with_context(report_pdf_no_attachment=True)
                ._render_qweb_pdf(
                    "hr_expense_meal_allowance.action_report_hr_expense_meal_allowance",
                    [expense.id],
                )
            )
            attachment_model.create(
                {
                    "name": attachment_name,
                    "raw": pdf_content,
                    "res_model": "hr.expense",
                    "res_id": expense.id,
                    "mimetype": "application/pdf",
                }
            )
