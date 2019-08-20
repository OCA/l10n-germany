# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

from .l10n_de_tax_statement_2018 import \
    _base_display_2018, _tax_display_2018, \
    _group_display_2018, _total_display_2018, _editable_display_2018
from .l10n_de_tax_statement_2019 import \
    _base_display_2019, _tax_display_2019, \
    _group_display_2019, _total_display_2019, _editable_display_2019


class VatStatementLine(models.Model):
    _name = 'l10n.de.tax.statement.line'
    _description = 'German Vat Statement Line'
    _order = 'code'

    name = fields.Char()
    code = fields.Char()

    statement_id = fields.Many2one(
        'l10n.de.tax.statement',
        'Statement'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='statement_id.company_id.currency_id',
        readonly=True,
        help='Utility field to express amount currency'
    )
    base = fields.Monetary()
    tax = fields.Monetary()
    format_base = fields.Char(compute='_compute_amount_format')
    format_tax = fields.Char(compute='_compute_amount_format')

    is_group = fields.Boolean(compute='_compute_is_group')
    is_total = fields.Boolean(compute='_compute_is_group')
    is_readonly = fields.Boolean(compute='_compute_is_readonly')

    @api.multi
    @api.depends('base', 'tax', 'code')
    def _compute_amount_format(self):
        for line in self:
            if line.statement_id.version == '2019':
                base_display = _base_display_2019()
                tax_display = _tax_display_2019()
            else:
                base_display = _base_display_2018()
                tax_display = _tax_display_2018()

            base = formatLang(self.env, line.base, monetary=True)
            tax = formatLang(self.env, line.tax, monetary=True)
            if line.code in base_display:
                line.format_base = base
            if line.code in tax_display:
                line.format_tax = tax

    @api.multi
    @api.depends('code')
    def _compute_is_group(self):
        for line in self:
            if line.statement_id.version == '2019':
                group_display = _group_display_2019()
                total_display = _total_display_2019()
            else:
                group_display = _group_display_2018()
                total_display = _total_display_2018()

            line.is_group = line.code in group_display
            line.is_total = line.code in total_display

    @api.multi
    @api.depends('code')
    def _compute_is_readonly(self):
        for line in self:
            if line.statement_id.version == '2019':
                editable_display = _editable_display_2019()
            else:
                editable_display = _editable_display_2018()

            if line.statement_id.state == 'draft':
                line.is_readonly = line.code not in editable_display
            else:
                line.is_readonly = True

    @api.multi
    def unlink(self):
        for line in self:
            if line.statement_id.state == 'posted':
                raise UserError(
                    _('You cannot delete lines of a posted statement! '
                      'Reset the statement to draft first.'))
            if line.statement_id.state == 'final':
                raise UserError(
                    _('You cannot delete lines of a statement set as final!'))
        super().unlink()

    @api.multi
    def view_tax_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='tax')

    @api.multi
    def view_base_lines(self):
        self.ensure_one()
        return self.get_lines_action(tax_or_base='base')

    def get_lines_action(self, tax_or_base='tax'):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_tree')
        vals = action.read()[0]
        vals['context'] = {}
        vals['domain'] = self._get_move_lines_domain(tax_or_base)
        return vals

    def _get_move_lines_domain(self, tax_or_base):
        statement = self.statement_id
        taxes = self._filter_taxes_by_code(statement._compute_taxes())
        past_taxes = statement._compute_past_invoices_taxes()
        past_taxes = self._filter_taxes_by_code(past_taxes)
        if statement.state == 'draft':
            domain = self._get_domain_draft(taxes, tax_or_base)
            past_domain = self._get_domain_draft(past_taxes, tax_or_base)
        else:
            domain = self._get_domain_posted(taxes, tax_or_base)
            past_domain = self._get_domain_posted(past_taxes, tax_or_base)
        curr_amls = self.env['account.move.line'].search(domain)
        past_amls = self.env['account.move.line'].search(past_domain)
        res = [('id', 'in', past_amls.ids + curr_amls.ids)]
        return res

    def _filter_taxes_by_code(self, taxes):
        self.ensure_one()
        tags_map = self.statement_id._get_tags_map()
        filtered_taxes = self.env['account.tax']
        for tax in taxes:
            for tag in tax.tag_ids:
                tag_map = tags_map.get(tag.id)
                if tag_map and tag_map[0] == self.code:
                    filtered_taxes |= tax
        return filtered_taxes.with_context(taxes.env.context)

    def _get_domain_draft(self, taxes, tax_or_base):
        self.ensure_one()
        ctx = taxes.env.context.copy()
        ctx.update({
            'l10n_de_statement_tax_ids': taxes.ids
        })
        AccountTax = self.env['account.tax'].with_context(ctx)
        return AccountTax.get_move_lines_domain(tax_or_base=tax_or_base)

    def _get_domain_posted(self, taxes, tax_or_base):
        self.ensure_one()
        statement = self.statement_id
        domain = [('move_id.l10n_de_tax_statement_id', '=', statement.id)]
        if tax_or_base == 'tax':
            tax_domain = [('tax_line_id', 'in', taxes.ids)]
        else:
            tax_domain = [('tax_ids', 'in', taxes.ids)]
        return expression.AND([domain, tax_domain])
