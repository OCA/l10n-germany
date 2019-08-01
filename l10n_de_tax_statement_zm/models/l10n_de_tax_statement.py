# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class VatStatement(models.Model):
    _inherit = 'l10n.de.tax.statement'

    tag_41_base = fields.Many2one(
        'account.account.tag',
        compute='_compute_tag_41'
    )
    tag_21_base = fields.Many2one(
        'account.account.tag',
        compute='_compute_tag_41'
    )
    zm_line_ids = fields.One2many(
        'l10n.de.tax.statement.zm.line',
        'statement_id',
        string='ZM Lines',
        readonly=True
    )
    zm_total = fields.Monetary(
        string='Total ZM amount',
        readonly=True,
        help='Total amount in currency of the statement.'
    )

    @api.depends('company_id')
    def _compute_tag_41(self):
        '''Computes Tag 41'''
        for statement in self:
            config = self.env['l10n.de.tax.statement.config'].search([
                ('company_id', '=', statement.company_id.id)
            ], limit=1)
            statement.tag_41_base = config.tag_41_base
            statement.tag_21_base = config.tag_21_base

    def _compute_zm_lines(self):
        '''Computes ZM lines for the report'''
        ZmLine = self.env['l10n.de.tax.statement.zm.line']
        for statement in self:
            statement.zm_line_ids.unlink()
            statement.zm_total = 0.0
            amounts_map = statement._get_partner_amounts_map()
            for partner_id in amounts_map:
                zm_values = self._prepare_zm_line(amounts_map[partner_id])
                zm_values['partner_id'] = partner_id
                zm_values['statement_id'] = statement.id
                newline = ZmLine.create(zm_values)
                statement.zm_line_ids += newline
                zm_total = newline.amount_products + newline.amount_services
                statement.zm_total += zm_total

    @api.model
    def _prepare_zm_line(self, partner_amounts):
        ''' Prepares an internal data structure representing the ZM line'''
        return {
            'country_code': partner_amounts['country_code'],
            'vat': partner_amounts['vat'],
            'amount_products': partner_amounts['amount_products'],
            'amount_services': partner_amounts['amount_services'],
            'currency_id': partner_amounts['currency_id'],
        }

    def _is_41_line(self, line):
        self.ensure_one()

        tag_41 = self.tag_41_base
        tags = line.tax_ids.mapped('tag_ids')
        if any(tags.filtered(lambda r: r == tag_41)):
            return True
        return False

    def _is_21_line(self, line):
        self.ensure_one()

        tag_21 = self.tag_21_base
        tags = line.tax_ids.mapped('tag_ids')
        if any(tags.filtered(lambda r: r == tag_21)):
            return True
        return False

    def _get_partner_amounts_map(self):
        ''' Generate an internal data structure representing the ICP line'''
        self.ensure_one()

        partner_amounts_map = {}
        for line in self.move_line_ids:
            is_41 = self._is_41_line(line)
            is_21 = self._is_21_line(line)
            if is_41 or is_21:
                vals = self._prepare_zm_line_from_move_line(line)
                if vals['partner_id'] not in partner_amounts_map:
                    self._init_partner_amounts_map(partner_amounts_map, vals)
                self._update_partner_amounts_map(partner_amounts_map, vals)
        return partner_amounts_map

    def _check_config_tag_41(self):
        ''' Checks the tag 41, as configured for the tax statement'''
        if self.env.context.get('skip_check_config_tag_41'):
            return
        for statement in self:
            if not statement.tag_41_base:
                raise UserError(
                    _('Tag 41 not configured for this Company! '
                      'Check the German Tax Tags Configuration.'))

    @api.multi
    def _check_config_tag_21(self):
        ''' Checks the tag 21, as configured for the tax statement'''
        if self.env.context.get('skip_check_config_tag_21'):
            return
        for statement in self:
            if not statement.tag_21_base:
                raise UserError(
                    _('Tag 21 not configured for this Company! '
                      'Check the German Tax Tags Configuration.'))

    @classmethod
    def _update_partner_amounts_map(cls, partner_amounts_map, vals):
        ''' Update amounts of the internal ICP lines data structure'''
        map_data = partner_amounts_map[vals['partner_id']]
        map_data['amount_products'] += vals['amount_products']
        map_data['amount_services'] += vals['amount_services']

    @classmethod
    def _init_partner_amounts_map(cls, partner_amounts_map, vals):
        ''' Initialize the internal ICP lines data structure'''
        partner_amounts_map[vals['partner_id']] = {
            'country_code': vals['country_code'],
            'vat': vals['vat'],
            'currency_id': vals['currency_id'],
            'amount_products': 0.0,
            'amount_services': 0.0,
        }

    def _prepare_zm_line_from_move_line(self, line):
        ''' Gets move line details and prepares ZM report line data'''
        self.ensure_one()

        balance = line.balance and -line.balance or 0
        if line.company_currency_id != self.currency_id:
            balance = line.company_currency_id.with_context(
                date=line.date
            ).compute(balance, self.currency_id, round=True)
        amount_products = balance
        amount_services = 0.0
        if self._is_21_line(line):
            amount_products = 0.0
            amount_services = balance

        return {
            'partner_id': line.partner_id.id,
            'country_code': line.partner_id.country_id.code,
            'vat': line.partner_id.vat,
            'amount_products': amount_products,
            'amount_services': amount_services,
            'currency_id': self.currency_id.id,
        }

    def reset(self):
        ''' Removes ZM lines if reset to draft'''
        self.mapped('zm_line_ids').unlink()
        return super().reset()

    def post(self):
        ''' Checks configuration when validating the statement'''
        self.ensure_one()
        self._check_config_tag_41()
        self._check_config_tag_21()
        res = super().post()
        self._compute_zm_lines()
        return res

    @api.model
    def _modifiable_values_when_posted(self):
        ''' Returns the modifiable fields even when the statement is posted'''
        res = super()._modifiable_values_when_posted()
        res.append('zm_line_ids')
        res.append('zm_total')
        return res

    def zm_update(self):
        ''' Update button'''
        self.ensure_one()

        if self.state in ['final']:
            raise UserError(
                _('You cannot modify a final statement!'))

        # clean old lines
        self.zm_line_ids.unlink()

        # check config
        self._check_config_tag_41()
        self._check_config_tag_21()

        # create lines
        self._compute_zm_lines()
