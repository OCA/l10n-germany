# Copyright 2020 sewisoft (<https://sewisoft.de>)
# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.tools.misc import formatLang
from odoo.exceptions import ValidationError


class VatStatementZmLine(models.Model):
    _name = 'l10n.de.tax.statement.zm.line'
    _description = 'Intra-Community transactions (ZM) line'
    _order = 'partner_id, country_code'

    statement_id = fields.Many2one(
        'l10n.de.tax.statement',
        'Statement',
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        readonly=True,
        required=True,
    )
    vat = fields.Char(
        string='VAT',
        readonly=True,
    )
    country_code = fields.Char(
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True
    )
    amount_products = fields.Monetary(readonly=True)
    format_amount_products = fields.Char(compute='_compute_zm_amount_format')
    amount_services = fields.Monetary(readonly=True)
    format_amount_services = fields.Char(compute='_compute_zm_amount_format')

    @api.depends('amount_products', 'amount_services')
    def _compute_zm_amount_format(self):
        for line in self:
            amount_products = formatLang(
                self.env, line.amount_products, monetary=True)
            amount_services = formatLang(
                self.env, line.amount_services, monetary=True)
            line.format_amount_products = amount_products
            line.format_amount_services = amount_services

    @api.constrains('country_code')
    def _check_country_code(self):
        europe_codes = self.env.ref('base.europe').country_ids.mapped('code')
        de_code = self.env.ref('base.de').code
        for line in self:
            country_codes = line.mapped('country_code')
            if de_code in country_codes:
                raise ValidationError(_(
                    'Wrong country code (DE) for ZM report'
                    ' at partner "{partner}" ({ref}) with vat "{vat}".').format(
                    partner=line.partner_id.name,
                    ref=line.partner_id.ref,
                    vat=line.partner_id.vat
                ))
            for code in country_codes:
                if code not in europe_codes:
                    raise ValidationError(_(
                        'Wrong country code ({code}) for ZM report'
                        ' at partner "{partner}" ({ref}) with vat "{vat}". '
                        'Please check your configuration.').format(
                        code=code,
                        partner=line.partner_id.name,
                        ref=line.partner_id.ref,
                        vat=line.partner_id.vat
                    ))
