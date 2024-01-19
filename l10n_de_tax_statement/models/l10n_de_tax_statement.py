# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

from .l10n_de_tax_statement_2018 import (
    _finalize_lines_2018,
    _map_tax_code_line_code_2018,
    _tax_statement_dict_2018,
    _totals_2018,
)
from .l10n_de_tax_statement_2019 import (
    _finalize_lines_2019,
    _map_tax_code_line_code_2019,
    _tax_statement_dict_2019,
    _totals_2019,
)
from .l10n_de_tax_statement_2021 import (
    _finalize_lines_2021,
    _map_tax_code_line_code_2021,
    _tax_statement_dict_2021,
    _totals_2021,
)


class VatStatement(models.Model):
    _name = "l10n.de.tax.statement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "German Vat Statement"

    name = fields.Char(
        string="Tax Statement",
        required=True,
        compute="_compute_name",
        store=True,
        readonly=False,
    )
    version = fields.Selection(
        [("2018", "2018"), ("2019", "2019/2020"), ("2021", "2021/2022")], required=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("posted", "Posted"), ("final", "Final")],
        readonly=True,
        default="draft",
        copy=False,
        string="Status",
    )
    line_ids = fields.One2many("l10n.de.tax.statement.line", "statement_id", "Lines")
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    from_date = fields.Date(
        required=True, store=True, readonly=False, compute="_compute_date_range"
    )
    to_date = fields.Date(
        required=True, store=True, readonly=False, compute="_compute_date_range"
    )
    date_range_id = fields.Many2one("date.range", "Date range")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    date_posted = fields.Datetime(readonly=True)
    date_update = fields.Datetime(readonly=True)

    tax_total = fields.Monetary(
        compute="_compute_tax_total", string="Verbl. Ust.-Vorauszahlung"
    )
    format_tax_total = fields.Char(
        compute="_compute_amount_format_tax_total",
    )
    move_line_ids = fields.One2many(
        "account.move.line",
        "l10n_de_tax_statement_id",
        string="Entry Lines",
        readonly=True,
    )

    @api.depends(
        "unreported_move_from_date",
        "is_invoice_basis",
        "company_id",
        "from_date",
        "to_date",
    )
    def _compute_unreported_move_ids(self):
        for statement in self:
            domain = statement._get_unreported_move_domain()
            move_lines = self.env["account.move.line"].search(domain)
            moves = move_lines.mapped("move_id").sorted("date")
            statement.unreported_move_ids = moves

    def _init_move_line_domain(self):
        return [
            ("move_id.company_id", "=", self.company_id.id),
            ("move_id.l10n_de_tax_statement_id", "=", False),
            ("move_id.state", "=", "posted"),
            "|",
            ("tax_ids", "!=", False),
            ("tax_line_id", "!=", False),
        ]

    def _get_unreported_move_domain(self):
        self.ensure_one()
        domain = self._init_move_line_domain()
        if self.is_invoice_basis and not self.unreported_move_from_date:
            domain += [
                "|",
                "&",
                ("move_id.invoice_date", "=", False),
                ("date", "<", self.from_date),
                "&",
                ("move_id.invoice_date", "!=", False),
                ("move_id.invoice_date", "<", self.from_date),
            ]
        elif self.is_invoice_basis and self.unreported_move_from_date:
            domain += [
                "|",
                "&",
                "&",
                ("move_id.invoice_date", "=", False),
                ("date", "<", self.from_date),
                ("date", ">=", self.unreported_move_from_date),
                "&",
                "&",
                ("move_id.invoice_date", "!=", False),
                ("move_id.invoice_date", "<", self.from_date),
                ("move_id.invoice_date", ">=", self.unreported_move_from_date),
            ]
        else:
            domain += [("date", "<", self.from_date)]
            if self.unreported_move_from_date:
                domain += [("date", ">=", self.unreported_move_from_date)]
        return domain

    unreported_move_ids = fields.One2many(
        "account.move",
        string="Unreported Journal Entries",
        compute="_compute_unreported_move_ids",
    )
    unreported_move_from_date = fields.Date(
        compute="_compute_unreported_move_from_date", store=True, readonly=False
    )
    is_invoice_basis = fields.Boolean(
        string="DE Tax Invoice Basis", related="company_id.l10n_de_tax_invoice_basis"
    )

    @api.depends("tax_total")
    def _compute_amount_format_tax_total(self):
        for statement in self:
            tax = formatLang(self.env, statement.tax_total, monetary=True)
            statement.format_tax_total = tax

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        fy_dates = self.env.company.compute_fiscalyear_dates(datetime.now())
        defaults.setdefault("from_date", fy_dates["date_from"])
        defaults.setdefault("to_date", fy_dates["date_to"])
        defaults.setdefault("name", self.env.company.name)
        return defaults

    @api.depends("date_range_id")
    def _compute_date_range(self):
        for statement in self:
            if statement.date_range_id and statement.state == "draft":
                statement.from_date = statement.date_range_id.date_start
                statement.to_date = statement.date_range_id.date_end
            statement.from_date = statement.from_date
            statement.to_date = statement.to_date

    @api.depends("from_date", "to_date")
    def _compute_name(self):
        for statement in self:
            display_name = statement.company_id.name
            if statement.from_date and statement.to_date:
                from_date = fields.Date.to_string(statement.from_date)
                to_date = fields.Date.to_string(statement.to_date)
                display_name += ": " + " ".join([from_date, to_date])
            statement.name = display_name

    @api.depends("from_date")
    def _compute_unreported_move_from_date(self):
        # by default the unreported_move_from_date is set to
        # a quarter (three months) before the from_date of the statement
        for statement in self:
            date_from = (
                statement.from_date + relativedelta(months=-3, day=1)
                if statement.from_date
                else False
            )
            statement.unreported_move_from_date = date_from

    @api.model
    def _prepare_lines(self):
        self.ensure_one()

        if self.version == "2021":
            lines = _tax_statement_dict_2021()
        elif self.version == "2019":
            lines = _tax_statement_dict_2019()
        else:
            lines = _tax_statement_dict_2018()

        return lines

    def _finalize_lines(self, lines):
        self.ensure_one()
        if self.version == "2021":
            lines = _finalize_lines_2021(lines)
        elif self.version == "2019":
            lines = _finalize_lines_2019(lines)
        else:
            lines = _finalize_lines_2018(lines)

        return lines

    def _get_tags_map(self):
        country_de = self.env.ref("base.de")
        de_tags = self.env["account.account.tag"].search(
            [("country_id", "=", country_de.id), ("applicability", "=", "taxes")]
        )
        if not de_tags:
            raise UserError(
                _(
                    "Tags mapping not configured for Germany! "
                    "Check the DE Tax Tags Configuration."
                )
            )
        pattern_code = re.compile(r"[+,-]?\d\w")
        matching = {}
        for tag in de_tags:
            res_code = pattern_code.match(tag.name)
            if re.search("tax", tag.name, re.IGNORECASE):
                matching.update({tag.id: (res_code.group(0), "tax")})
            elif re.search("base", tag.name, re.IGNORECASE):
                matching.update({tag.id: (res_code.group(0), "base")})
            elif res_code:
                matching.update({tag.id: (res_code.group(0), False)})
        return matching

    def statement_update(self):
        self.ensure_one()

        if self.state in ["posted", "final"]:
            raise UserError(_("You cannot modify a posted statement!"))

        # clean old lines
        self.line_ids.unlink()

        # calculate lines
        lines = self._prepare_lines()
        move_lines = self._compute_move_lines()
        self._set_statement_lines(lines, move_lines)
        move_lines = self._compute_past_invoices_move_lines()
        self._set_statement_lines(lines, move_lines)
        self._finalize_lines(lines)

        # create lines
        self.write(
            {
                "line_ids": [(0, 0, line) for line in lines.values()],
                "date_update": fields.Datetime.now(),
            }
        )

    def _compute_past_invoices_move_lines(self):
        self.ensure_one()
        moves_to_include = self.unreported_move_ids.filtered(
            lambda m: m.l10n_de_tax_statement_include
        )
        return moves_to_include.line_ids

    def _compute_move_lines(self):
        self.ensure_one()
        domain = self._get_move_lines_domain()
        return self.env["account.move.line"].search(domain)

    def _match_no_tag(self, lines, move_line, tags_map):
        rep_line = move_line.tax_repartition_line_id
        if rep_line and not rep_line.tag_ids:
            # Workaround missing repartition tag
            if rep_line.invoice_tax_id:
                tax_id = rep_line.invoice_tax_id

                siblings = tax_id.invoice_repartition_line_ids
            elif rep_line.refund_tax_id:
                tax_id = rep_line.refund_tax_id

                siblings = tax_id.refund_repartition_line_ids
            else:
                return False, False

            for sibling in siblings.filtered_domain([("tag_ids", "!=", False)]):
                for tag in sibling.tag_ids:
                    tag_map = tags_map.get(tag.id)
                    if tag_map:
                        code, column = tag_map
                        code = self._strip_sign_in_tag_code(code)
                        line_code = self.map_tax_code_line_code(code)
                        if not line_code:
                            continue
                        # Flip column, to pick the other if only one has a tag
                        if column == "tax":
                            column = "base"
                        else:
                            column = "tax"

                        # Special case, otherwise 62 appears twice and sums up to zero
                        if code == "62":
                            return False, False

                        return line_code, column

        return False, False

    def _set_statement_lines(self, lines, move_lines):
        self.ensure_one()
        tags_map = self._get_tags_map()
        for line in move_lines:
            if not line.tax_tag_ids:
                line_code, column = self._match_no_tag(lines, line, tags_map)
                if line_code and column:
                    lines[line_code][column] -= line.balance

            for tag in line.tax_tag_ids:
                tag_map = tags_map.get(tag.id)
                if tag_map:
                    code, column = tag_map
                    code = self._strip_sign_in_tag_code(code)
                    line_code = self.map_tax_code_line_code(code)
                    if not line_code:
                        raise UserError(
                            _(
                                "This tax code for Germany is not supported! "
                                "Check the DE Tax Tags Configuration."
                            )
                        )
                    if not column:
                        if "base" in lines[line_code]:
                            column = "base"
                        else:
                            column = "tax"

                    # Workaround for falsely-tagged tax
                    if column == "base" and code in ("85", "47", "74"):
                        column = "tax"

                    lines[line_code][column] -= line.balance

    def finalize(self):
        self.ensure_one()
        self.write({"state": "final"})

    def post(self):
        self.ensure_one()

        prev_open_statements = self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("state", "=", "draft"),
                ("id", "<", self.id),
            ],
            limit=1,
        )

        if prev_open_statements:
            raise UserError(
                _(
                    "You cannot post a statement if all the previous "
                    "statements are not yet posted! "
                    "Please Post all the other statements first."
                )
            )

        self.write({"state": "posted", "date_posted": fields.Datetime.now()})
        self.unreported_move_ids.filtered(
            lambda m: m.l10n_de_tax_statement_include
        ).write({"l10n_de_tax_statement_id": self.id})
        self.unreported_move_ids.flush_recordset()
        move_lines = self._compute_move_lines()
        move_lines.move_id.write({"l10n_de_tax_statement_id": self.id})
        move_lines.move_id.flush_recordset()

    def _get_move_lines_domain(self):
        domain = self._init_move_line_domain()
        if self.is_invoice_basis:
            domain += [
                "|",
                "&",
                "&",
                ("move_id.invoice_date", "=", False),
                ("date", "<=", self.to_date),
                ("date", ">=", self.from_date),
                "&",
                "&",
                ("move_id.invoice_date", "!=", False),
                ("move_id.invoice_date", "<=", self.to_date),
                ("move_id.invoice_date", ">=", self.from_date),
            ]
        else:
            domain += [("date", "<=", self.to_date), ("date", ">=", self.from_date)]
        return domain

    def reset(self):
        self.write({"state": "draft", "date_posted": None})
        req = """
            UPDATE account_move_line
            SET l10n_de_tax_statement_id = NULL
            WHERE
              l10n_de_tax_statement_id = %s
        """
        self.env.cr.execute(req, (self.id,))

    def _modifiable_values_when_posted(self):
        return ["state"]

    def write(self, values):
        for statement in self:
            if statement.state == "final":
                raise UserError(_("You cannot modify a statement set as final!"))
            if "state" not in values or values["state"] != "draft":
                if statement.state == "posted":
                    for val in values:
                        if val not in self._modifiable_values_when_posted():
                            raise UserError(
                                _(
                                    "You cannot modify a posted statement! "
                                    "Reset the statement to draft first."
                                )
                            )
        return super().write(values)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_if_posted_or_final(self):
        for statement in self:
            if statement.state == "posted":
                raise UserError(
                    _(
                        "You cannot delete a posted statement! "
                        "Reset the statement to draft first."
                    )
                )
            if statement.state == "final":
                raise UserError(_("You cannot delete a statement set as final!"))

    @api.depends("line_ids.tax")
    def _compute_tax_total(self):
        for statement in self:
            lines = statement.line_ids

            if statement.version == "2021":
                list_totals = _totals_2021()
            elif statement.version == "2019":
                list_totals = _totals_2019()
            else:
                list_totals = _totals_2018()

            total_lines = lines.filtered(lambda l: l.code in list_totals)
            statement.tax_total = sum(line.tax for line in total_lines)

    def _get_all_statement_move_lines(self):
        self.ensure_one()
        if self.state == "draft":
            curr_amls = self._compute_move_lines()
            past_amls = self._compute_past_invoices_move_lines()
            all_amls = curr_amls | past_amls
        else:
            all_amls = self.move_line_ids
        return all_amls

    def map_tax_code_line_code(self, code):
        self.ensure_one()
        if self.version == "2021":
            map_tax_line_code = _map_tax_code_line_code_2021()
        elif self.version == "2019":
            map_tax_line_code = _map_tax_code_line_code_2019()
        else:
            map_tax_line_code = _map_tax_code_line_code_2018()
        line_code = map_tax_line_code.get(code)
        return line_code

    @api.model
    def _strip_sign_in_tag_code(self, code):
        if code[0:1] in ["+", "-"]:
            code = code[1:]
        return code
