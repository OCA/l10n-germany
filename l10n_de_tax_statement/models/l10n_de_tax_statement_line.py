# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .elster_config import (
    DEDUCTIBLE,
    INFO,
    OTHER_TAGS_SECTION,
    ROW_TAGS,
    STATEMENT_ROWS,
)


class L10nDeTaxStatementLine(models.Model):
    _name = "l10n.de.tax.statement.line"
    _description = "German VAT Statement Line"
    _order = "statement_id, sequence, id"

    statement_id = fields.Many2one(
        "l10n.de.tax.statement", required=True, index=True, ondelete="cascade"
    )
    currency_id = fields.Many2one(related="statement_id.currency_id")
    sequence = fields.Integer()
    display_type = fields.Selection([("line_section", "Section")])
    name = fields.Char()
    base_code = fields.Char("Kz Base")
    base_tag = fields.Char(help="Tax tag the base sums up, without its sign")
    base = fields.Monetary()
    tax_code = fields.Char("Kz Tax")
    tax_tag = fields.Char(help="Tax tag the tax sums up, without its sign")
    tax = fields.Monetary()
    kind = fields.Integer(help="How the tax adds up to Kennzahl 83")

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.statement_id._check_draft()
        return lines

    def write(self, vals):
        self.statement_id._check_draft()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft(self):
        self.statement_id._check_draft()

    def _get_journal_items_action(self, tag):
        self.ensure_one()
        tags = self.env["account.account.tag"]._get_tax_tags(
            tag, self.env.ref("base.de").id
        )
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_account_moves_all_tree"
        )
        action["domain"] = self.statement_id._get_journal_items_domain() + [
            ("tax_tag_ids", "in", tags.ids)
        ]
        action["context"] = {}
        return action

    def action_view_base_items(self):
        return self._get_journal_items_action(self.base_tag)

    def action_view_tax_items(self):
        return self._get_journal_items_action(self.tax_tag)

    @api.model
    def _prepare_vals(self, amounts):
        """Return the values of the rows of the ELSTER form, filled with the
        amounts of the tax tags of the period. The amounts of tax tags without
        a row follow in a section of their own, they aren't declared."""
        vals_list = []
        for row in STATEMENT_ROWS:
            vals = {
                key: value
                for key, value in row.items()
                if key not in ("xml", "not_negative")
            }
            if vals.get("base_tag"):
                vals["base"] = amounts.get(vals["base_tag"], 0.0)
            if vals.get("tax_tag"):
                # Odoo books input tax negatively, ELSTER wants it positive
                sign = -1 if vals["kind"] == DEDUCTIBLE else 1
                vals["tax"] = sign * amounts.get(vals["tax_tag"], 0.0)
            vals_list.append(vals)
        other_tags = sorted(
            tag for tag, amount in amounts.items() if tag not in ROW_TAGS and amount
        )
        if other_tags:
            vals_list.append(
                {"display_type": "line_section", "name": OTHER_TAGS_SECTION}
            )
        for tag in other_tags:
            vals_list.append(
                {"name": tag, "base_tag": tag, "base": amounts[tag], "kind": INFO}
            )
        for sequence, vals in enumerate(vals_list):
            vals["sequence"] = sequence
        return vals_list
