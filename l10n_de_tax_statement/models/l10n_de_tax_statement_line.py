# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

from .l10n_de_tax_statement_2018 import (
    _base_display_2018,
    _editable_display_2018,
    _group_display_2018,
    _tax_display_2018,
    _total_display_2018,
)
from .l10n_de_tax_statement_2019 import (
    _base_display_2019,
    _editable_display_2019,
    _group_display_2019,
    _tax_display_2019,
    _total_display_2019,
)


class VatStatementLine(models.Model):
    _name = "l10n.de.tax.statement.line"
    _description = "German Vat Statement Line"
    _order = "code"

    name = fields.Char()
    code = fields.Char()

    statement_id = fields.Many2one("l10n.de.tax.statement")
    currency_id = fields.Many2one(
        "res.currency",
        related="statement_id.company_id.currency_id",
        help="Utility field to express amount currency",
    )
    base = fields.Monetary()
    tax = fields.Monetary()
    format_base = fields.Char(compute="_compute_amount_format")
    format_tax = fields.Char(compute="_compute_amount_format")

    is_group = fields.Boolean(compute="_compute_is_group")
    is_total = fields.Boolean(compute="_compute_is_group")
    is_readonly = fields.Boolean(compute="_compute_is_readonly")

    @api.depends("base", "tax", "code")
    def _compute_amount_format(self):
        for line in self:
            if line.statement_id.version == "2019":
                base_display = _base_display_2019()
                tax_display = _tax_display_2019()
            else:
                base_display = _base_display_2018()
                tax_display = _tax_display_2018()

            base = formatLang(self.env, line.base, monetary=True)
            tax = formatLang(self.env, line.tax, monetary=True)
            line.format_base = False
            line.format_tax = False
            if line.code in base_display:
                line.format_base = base
            if line.code in tax_display:
                line.format_tax = tax

    @api.depends("code")
    def _compute_is_group(self):
        for line in self:
            if line.statement_id.version == "2019":
                group_display = _group_display_2019()
                total_display = _total_display_2019()
            else:
                group_display = _group_display_2018()
                total_display = _total_display_2018()

            line.is_group = line.code in group_display
            line.is_total = line.code in total_display

    @api.depends("code")
    def _compute_is_readonly(self):
        for line in self:
            if line.statement_id.version == "2019":
                editable_display = _editable_display_2019()
            else:
                editable_display = _editable_display_2018()

            if line.statement_id.state == "draft":
                line.is_readonly = line.code not in editable_display
            else:
                line.is_readonly = True

    def unlink(self):
        for line in self:
            if line.statement_id.state == "posted":
                raise UserError(
                    _(
                        "You cannot delete lines of a posted statement! "
                        "Reset the statement to draft first."
                    )
                )
            if line.statement_id.state == "final":
                raise UserError(
                    _("You cannot delete lines of a statement set as final!")
                )
        super().unlink()

    def view_tax_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="tax")

    def view_base_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base="base")

    def get_lines_action(self, tax_or_base="tax"):
        self.ensure_one()
        action = self.env.ref("account.action_account_moves_all_tree")
        vals = action.read()[0]
        vals["context"] = {}
        vals["domain"] = self._get_move_lines_domain(tax_or_base)
        return vals

    def _get_move_lines_domain(self, tax_or_base):
        all_amls = self.statement_id._get_all_statement_move_lines()
        domain_lines_ids = []
        tags_map = self.statement_id._get_tags_map()
        for line in all_amls:
            for tag in line.tag_ids:
                tag_map = tags_map.get(tag.id, ("", ""))
                code, column = tag_map
                code = self.statement_id._strip_sign_in_tag_code(code)
                line_code = self.statement_id.map_tax_code_line_code(code)
                if line_code and line_code == self.code:
                    if (tax_or_base == "tax" and column == "tax") or (
                        tax_or_base == "base" and column == "base"
                    ):
                        domain_lines_ids += [line.id]
        return [("id", "in", domain_lines_ids)]
