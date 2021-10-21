# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang

from .l10n_de_tax_statement_2018 import \
    _tax_statement_dict_2018, _finalize_lines_2018, \
    _get_tags_map_2018, _totals_2018
from .l10n_de_tax_statement_2019 import \
    _tax_statement_dict_2019, _finalize_lines_2019, \
    _get_tags_map_2019, _totals_2019


class VatStatement(models.Model):
    _name = 'l10n.de.tax.statement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'German Vat Statement'

    name = fields.Char(
        string='Tax Statement',
        required=True,
    )
    version = fields.Selection([
        ('2018', '2018'),
        ('2019', '2019'),
    ], required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('final', 'Final')],
        readonly=True,
        default='draft',
        copy=False,
        string='Status'
    )
    line_ids = fields.One2many(
        'l10n.de.tax.statement.line',
        'statement_id',
        'Lines'
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id
    )
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    date_range_id = fields.Many2one(
        'date.range',
        'Date range',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        readonly=True
    )
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')],
        'Target Moves',
        readonly=True,
        required=True,
        default='posted'
    )
    date_posted = fields.Datetime(readonly=True)
    date_update = fields.Datetime(readonly=True)

    tax_total = fields.Monetary(
        compute='_compute_tax_total',
        string='Verbl. Ust.-Vorauszahlung'
    )
    format_tax_total = fields.Char(
        compute='_compute_amount_format_tax_total',
    )
    move_line_ids = fields.One2many(
        'account.move.line',
        'l10n_de_tax_statement_id',
        string='Entry Lines',
        readonly=True,
    )

    @api.multi
    def _compute_unreported_move_ids(self):
        for statement in self:
            domain = statement._get_unreported_move_domain()
            move_lines = self.env['account.move.line'].search(domain)
            moves = move_lines.mapped('move_id').sorted('date')
            statement.unreported_move_ids = moves

    @api.multi
    def _get_unreported_move_domain(self):
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('invoice_id', '!=', False),
            ('l10n_de_tax_statement_id', '=', False),
            ('date', '<', self.from_date),
        ]
        if self.unreported_move_from_date:
            domain += [
                ('date', '>=', self.unreported_move_from_date),
            ]
        return domain

    unreported_move_ids = fields.One2many(
        'account.move',
        string="Unreported Journal Entries",
        compute='_compute_unreported_move_ids'
    )
    unreported_move_from_date = fields.Date()

    @api.multi
    @api.depends('tax_total')
    def _compute_amount_format_tax_total(self):
        for statement in self:
            tax = formatLang(self.env, statement.tax_total, monetary=True)
            statement.format_tax_total = tax

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        company = self.env.user.company_id
        fy_dates = company.compute_fiscalyear_dates(datetime.now())
        defaults.setdefault('from_date', fy_dates['date_from'])
        defaults.setdefault('to_date', fy_dates['date_to'])
        defaults.setdefault('name', company.name)
        return defaults

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id and self.state == 'draft':
            self.update({
                'from_date': self.date_range_id.date_start,
                'to_date': self.date_range_id.date_end,
            })

    @api.onchange('from_date', 'to_date')
    def onchange_date(self):
        display_name = self.company_id.name
        if self.from_date and self.to_date:
            from_date = fields.Date.to_string(self.from_date)
            to_date = fields.Date.to_string(self.to_date)
            display_name += ': ' + ' '.join([from_date, to_date])
        self.name = display_name

    @api.onchange('from_date')
    def onchange_date_from_date(self):
        # by default the unreported_move_from_date is set to
        # a quarter (three months) before the from_date of the statement
        date_from = self.from_date + relativedelta(months=-3, day=1)
        self.unreported_move_from_date = date_from

    @api.onchange('unreported_move_from_date')
    def onchange_unreported_move_from_date(self):
        self._compute_unreported_move_ids()

    @api.model
    def _get_taxes_domain(self):
        return [('has_moves', '=', True)]

    @api.model
    def _prepare_lines(self):
        self.ensure_one()

        if self.version == '2019':
            lines = _tax_statement_dict_2019()
        else:
            lines = _tax_statement_dict_2018()

        return lines

    def _finalize_lines(self, lines):
        self.ensure_one()
        if self.version == '2019':
            lines = _finalize_lines_2019(lines)
        else:
            lines = _finalize_lines_2018(lines)

        return lines

    def _get_tags_map(self):
        self.ensure_one()
        config = self.env['l10n.de.tax.statement.config'].search([
            ('company_id', '=', self.company_id.id)], limit=1
        )
        if not config:
            raise UserError(
                _('Tags mapping not configured for this Company! '
                  'Check the DE Tags Configuration.'))

        if self.version == '2019':
            config_map = _get_tags_map_2019(config)
        else:
            config_map = _get_tags_map_2018(config)

        return config_map

    @api.multi
    def statement_update(self):
        self.ensure_one()

        if self.state in ['posted', 'final']:
            raise UserError(_('You cannot modify a posted statement!'))

        # clean old lines
        self.line_ids.unlink()

        # calculate lines
        lines = self._prepare_lines()
        taxes = self._compute_taxes()
        self._set_statement_lines(lines, taxes)
        taxes = self._compute_past_invoices_taxes()
        self._set_statement_lines(lines, taxes)
        self._finalize_lines(lines)

        # create lines
        self.write({
            'line_ids': [(0, 0, line) for line in lines.values()],
            'date_update': fields.Datetime.now(),
        })

    def _compute_past_invoices_taxes(self):
        self.ensure_one()
        ctx = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
            'skip_invoice_basis_domain': True,
            'unreported_move': True,
            'unreported_move_from_date': self.unreported_move_from_date
        }
        taxes = self.env['account.tax'].with_context(ctx)
        for move in self.unreported_move_ids:
            for move_line in move.line_ids:
                if move_line.tax_exigible:
                    if move_line.tax_line_id:
                        taxes |= move_line.tax_line_id
                if move_line.tax_ids:
                    taxes |= move_line.tax_ids
        return taxes

    def _compute_taxes(self):
        self.ensure_one()
        ctx = {
            'from_date': self.from_date,
            'to_date': self.to_date,
            'target_move': self.target_move,
            'company_id': self.company_id.id,
        }
        domain = self._get_taxes_domain()
        taxes = self.env['account.tax'].with_context(ctx).search(domain)
        return taxes

    def _set_statement_lines(self, lines, taxes):
        self.ensure_one()
        tags_map = self._get_tags_map()
        for tax in taxes:
            for tag in tax.tag_ids:
                tag_map = tags_map.get(tag.id)
                if tag_map:
                    code, column = tag_map
                    if column == 'base':
                        lines[code][column] += tax.base_balance
                    else:
                        lines[code][column] += tax.balance

    @api.multi
    def finalize(self):
        self.ensure_one()
        self.write({
            'state': 'final'
        })

    @api.multi
    def post(self):
        self.ensure_one()
        prev_open_statements = self.search([
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'draft'),
            ('id', '<', self.id)
        ], limit=1)

        if prev_open_statements:
            raise UserError(
                _('You cannot post a statement if all the previous '
                  'statements are not yet posted! '
                  'Please Post all the other statements first.'))

        self.write({
            'state': 'posted',
            'date_posted': fields.Datetime.now()
        })
        self.unreported_move_ids.filtered(
            lambda m: m.l10n_de_tax_statement_include
        ).write({
            'l10n_de_tax_statement_id': self.id,
        })
        domain = [
            ('company_id', '=', self.company_id.id),
            ('l10n_de_tax_statement_id', '=', False),
            ('date', '<=', self.to_date),
            ('date', '>=', self.from_date),
        ]
        move_line_ids = self.env['account.move.line'].search(domain)
        updated_move_ids = move_line_ids.mapped('move_id')
        updated_move_ids.write({
            'l10n_de_tax_statement_id': self.id,
        })

    @api.multi
    def reset(self):
        self.write({
            'state': 'draft',
            'date_posted': None
        })
        req = """
            UPDATE account_move_line
            SET l10n_de_tax_statement_id = NULL
            WHERE
              l10n_de_tax_statement_id = %s
        """
        self.env.cr.execute(
            req, (self.id, ))

    @api.model
    def _modifiable_values_when_posted(self):
        return ['state']

    @api.multi
    def write(self, values):
        for statement in self:
            if statement.state == 'final':
                raise UserError(
                    _('You cannot modify a statement set as final!'))
            if 'state' not in values or values['state'] != 'draft':
                if statement.state == 'posted':
                    for val in values:
                        if val not in self._modifiable_values_when_posted():
                            raise UserError(
                                _('You cannot modify a posted statement! '
                                  'Reset the statement to draft first.'))
        return super().write(values)

    @api.multi
    def unlink(self):
        for statement in self:
            if statement.state == 'posted':
                raise UserError(
                    _('You cannot delete a posted statement! '
                      'Reset the statement to draft first.'))
            if statement.state == 'final':
                raise UserError(
                    _('You cannot delete a statement set as final!'))
        super().unlink()

    @api.depends('line_ids.tax')
    def _compute_tax_total(self):
        for statement in self:
            lines = statement.line_ids

            if statement.version == '2019':
                list_totals = _totals_2019()
            else:
                list_totals = _totals_2018()

            total_lines = lines.filtered(lambda l: l.code in list_totals)
            statement.tax_total = sum(line.tax for line in total_lines)
