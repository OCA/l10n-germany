# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

# The periods of the ELSTER form with its codes
PERIODS = [
    ("01", "January"),
    ("02", "February"),
    ("03", "March"),
    ("04", "April"),
    ("05", "May"),
    ("06", "June"),
    ("07", "July"),
    ("08", "August"),
    ("09", "September"),
    ("10", "October"),
    ("11", "November"),
    ("12", "December"),
    ("41", "1st Quarter"),
    ("42", "2nd Quarter"),
    ("43", "3rd Quarter"),
    ("44", "4th Quarter"),
]


class L10nDeTaxStatement(models.Model):
    _name = "l10n.de.tax.statement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "German VAT Statement"
    _order = "date_from desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.context_today(self).year,
        tracking=True,
    )
    period = fields.Selection(PERIODS, required=True, tracking=True)
    date_from = fields.Date(compute="_compute_dates", store=True)
    date_to = fields.Date(compute="_compute_dates", store=True)
    is_corrected = fields.Boolean(
        "Corrected Statement",
        tracking=True,
        help="Berichtigte Anmeldung: the statement corrects one already sent",
    )
    corrected_statement_id = fields.Many2one(
        "l10n.de.tax.statement",
        "Corrects",
        readonly=True,
        copy=False,
        help="The approved statement of the period which this corrected "
        "statement corrects, set on its approval. Empty if the period was "
        "declared outside of Odoo.",
    )
    state = fields.Selection(
        [("draft", "Draft"), ("approved", "Approved")],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
    )
    is_period_open = fields.Boolean(
        compute="_compute_is_period_open",
        help="The tax return lock date of the company doesn't cover the period",
    )
    line_ids = fields.One2many(
        "l10n.de.tax.statement.line", "statement_id", "Lines", copy=False
    )
    tax_total = fields.Monetary(
        "Remaining Advance Payment",
        compute="_compute_tax_total",
        store=True,
        help="Kennzahl 83: the remaining advance payment, a surplus if negative",
    )

    def _has_valid_year(self):
        """Whether the year has four digits, like ELSTER wants it"""
        self.ensure_one()
        return 1000 <= self.year <= 9999

    @api.constrains("year")
    def _check_year(self):
        for statement in self:
            if not statement._has_valid_year():
                raise ValidationError(self.env._("The year must have four digits."))

    @api.constrains("company_id", "year", "period", "is_corrected")
    def _check_unique_period(self):
        """A period is declared once, any further statement corrects it"""
        for statement in self.filtered(lambda st: not st.is_corrected):
            if self.search_count(
                statement._get_period_domain() + [("is_corrected", "=", False)]
            ):
                raise ValidationError(
                    self.env._(
                        "There is already a statement for %(name)s, create a "
                        "corrected statement instead.",
                        name=statement.name,
                    )
                )

    @api.depends("date_to", "company_id.tax_lock_date")
    def _compute_is_period_open(self):
        for statement in self:
            lock_date = statement.company_id.tax_lock_date
            statement.is_period_open = bool(statement.date_to) and (
                not lock_date or lock_date < statement.date_to
            )

    @api.depends("year", "period")
    def _compute_dates(self):
        for statement in self:
            if not statement.period or not statement._has_valid_year():
                statement.date_from = statement.date_to = False
                continue
            code = int(statement.period)
            if code > 40:
                date_from = date(statement.year, (code - 41) * 3 + 1, 1)
                months = 3
            else:
                date_from = date(statement.year, code, 1)
                months = 1
            statement.date_from = date_from
            statement.date_to = date_from + relativedelta(months=months, days=-1)

    @api.depends("year", "period", "is_corrected")
    def _compute_name(self):
        periods = dict(self._fields["period"]._description_selection(self.env))
        for statement in self:
            name = f"{periods.get(statement.period, '')} {statement.year or ''}"
            if statement.is_corrected:
                name = self.env._("%(name)s (corrected)", name=name.strip())
            statement.name = name.strip()

    @api.depends("line_ids.tax", "line_ids.kind")
    def _compute_tax_total(self):
        for statement in self:
            statement.tax_total = sum(
                line.tax * line.kind for line in statement.line_ids
            )

    def _check_draft(self):
        if any(statement.state != "draft" for statement in self):
            raise UserError(
                self.env._(
                    "You can only modify a draft statement, create a corrected "
                    "statement instead."
                )
            )

    def _check_write(self, vals):
        """Only a draft statement can change its period"""
        if vals.keys() & {"year", "period", "is_corrected", "company_id"}:
            self._check_draft()

    @api.model_create_multi
    def create(self, vals_list):
        statements = super().create(vals_list)
        statements._update_lines()
        return statements

    def write(self, vals):
        self._check_write(vals)
        res = super().write(vals)
        if vals.keys() & {"year", "period", "company_id"}:
            self._update_lines()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft(self):
        self._check_draft()

    def _get_journal_items_domain(self):
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("parent_state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]

    @api.model
    def _get_tag_balance(self, tag, tag_invert, balance):
        """Return the balance of journal items for the tax tag ``tag``, signed
        the same way as the tax report of Odoo does"""
        if tag_invert:
            balance = -balance
        return -balance if tag.tax_negate else balance

    def _get_tag_amounts(self):
        """Return the amounts of the period by tax tag name without its sign,
        signed the same way as the tax report of Odoo does"""
        self.ensure_one()
        tags = (
            self.env["account.account.tag"]
            .with_context(active_test=False, lang="en_US")
            .search(
                [
                    ("country_id", "=", self.env.ref("base.de").id),
                    ("applicability", "=", "taxes"),
                ]
            )
        )
        names = {tag: tag.name[1:] for tag in tags}
        groups = self.env["account.move.line"]._read_group(
            self._get_journal_items_domain() + [("tax_tag_ids", "in", tags.ids)],
            groupby=["tax_tag_ids", "tax_tag_invert"],
            aggregates=["balance:sum"],
        )
        amounts = defaultdict(float)
        for tag, tag_invert, balance in groups:
            if tag not in names:
                continue
            amounts[names[tag]] += self._get_tag_balance(tag, tag_invert, balance)
        return {
            name: self.currency_id.round(amount) for name, amount in amounts.items()
        }

    def _update_lines(self):
        """Compute the lines from the journal items of the period, extended by
        the modules which add lines of their own"""
        for statement in self:
            if not statement.date_from:
                continue
            vals_list = self.env["l10n.de.tax.statement.line"]._prepare_vals(
                statement._get_tag_amounts()
            )
            statement.line_ids = [Command.clear()] + [
                Command.create(vals) for vals in vals_list
            ]

    def action_update(self):
        self._check_draft()
        self._update_lines()

    def _get_lines_snapshot(self):
        """Return what the user checked: the lines with their amounts"""
        self.ensure_one()
        return [
            (
                line.display_type or "",
                line.name,
                line.base_tag or "",
                line.base,
                line.tax_tag or "",
                line.tax,
            )
            for line in self.line_ids.sorted("sequence")
        ]

    def _check_lines_current(self):
        """Compute the lines again and make sure they didn't change since the
        user checked them, e.g. because of journal items posted meanwhile"""
        self.ensure_one()
        snapshot = self._get_lines_snapshot()
        self._update_lines()
        if self._get_lines_snapshot() != snapshot:
            raise UserError(
                self.env._(
                    "The journal items of the period changed since the lines "
                    "were computed. Press Update and check the lines again."
                )
            )

    def _check_approve_access(self):
        """Only accounting administrators declare the statement, the button
        hides it, the server makes sure of it"""
        if not self.env.user.has_group("account.group_account_manager"):
            raise AccessError(
                self.env._("Only accounting administrators can approve a statement.")
            )

    def _get_period_domain(self):
        self.ensure_one()
        return [
            ("id", "!=", self.id),
            ("company_id", "=", self.company_id.id),
            ("year", "=", self.year),
            ("period", "=", self.period),
        ]

    def _check_corrected(self):
        """A corrected statement corrects a declared period: the statement of
        the period must not be a draft. It may have been declared outside of
        Odoo, then there is none."""
        self.ensure_one()
        if not self.is_corrected:
            return
        draft = self.search(
            self._get_period_domain()
            + [("is_corrected", "=", False), ("state", "=", "draft")],
            limit=1,
        )
        if draft:
            raise UserError(
                self.env._(
                    "The statement %(name)s isn't approved yet: update and "
                    "approve it instead of correcting it.",
                    name=draft.name,
                )
            )

    def _check_approve(self):
        self.ensure_one()
        self._check_approve_access()
        self._check_draft()
        self._check_corrected()
        self._check_lines_current()

    def _get_upload_attachments(self):
        """Return the files to upload to ELSTER, extended by the modules which
        add declarations"""
        return self._create_elster_xml_attachment()

    def _get_approve_attachments(self):
        """Return the files of the approval: the files to upload to ELSTER,
        unless a module sends the statement itself"""
        return self._get_upload_attachments()

    def _get_approve_message(self):
        return self.env._(
            "The statement is approved. Upload the attached files to ELSTER."
        )

    def _action_approve(self):
        """Approve the checked statement, extended by the modules which send
        the statement"""
        vals = {"state": "approved"}
        if self.is_corrected:
            vals["corrected_statement_id"] = self.search(
                self._get_period_domain() + [("state", "=", "approved")],
                order="id desc",
                limit=1,
            ).id
        self.write(vals)

    def _post_approve_message(self):
        self.ensure_one()
        self.message_post(
            body=self._get_approve_message(),
            attachment_ids=self._get_approve_attachments().ids,
        )

    def action_approve(self):
        """Approve the statement: it is final and declared"""
        self.ensure_one()
        self._check_approve()
        self._action_approve()
        self._post_approve_message()
        return True
