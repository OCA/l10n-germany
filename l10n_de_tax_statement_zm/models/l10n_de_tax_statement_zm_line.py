# Copyright 2020 sewisoft (<https://sewisoft.de>)
# Copyright 2018 Onestein (<http://www.onestein.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class L10nDeTaxStatementZmLine(models.Model):
    _name = "l10n.de.tax.statement.zm.line"
    _description = "Intra-Community transactions (ZM) line"
    _order = "partner_id, country_code"

    statement_id = fields.Many2one(
        "l10n.de.tax.statement", "Statement", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", readonly=True, required=True)
    vat = fields.Char(readonly=True)
    country_code = fields.Char(readonly=True)
    currency_id = fields.Many2one(related="statement_id.currency_id")
    amount_products = fields.Monetary(readonly=True)
    amount_services = fields.Monetary(readonly=True)

    @api.model
    def _prepare_vals(self, partner, amounts):
        """Return the values of the ZM line of a partner with its amounts of
        products and services"""
        return {
            "partner_id": partner.id,
            "country_code": partner.country_id.code,
            "vat": partner.vat,
            "amount_products": amounts.get("amount_products", 0.0),
            "amount_services": amounts.get("amount_services", 0.0),
        }

    def _check_country_code(self):
        """Only customers of other EU countries belong to the ZM, checked
        when it is approved: a draft statement shows the wrong lines"""
        europe_codes = self.env.ref("base.europe").country_ids.mapped("code")
        for line in self:
            if line.country_code == "DE":
                raise UserError(
                    self.env._(
                        "Wrong country code (DE) for ZM report at partner "
                        '"%(partner)s" with VAT number "%(vat)s".',
                        partner=line.partner_id.name,
                        vat=line.partner_id.vat,
                    )
                )
            if line.country_code and line.country_code not in europe_codes:
                raise UserError(
                    self.env._(
                        "Wrong country code (%(code)s) for ZM report at partner "
                        '"%(partner)s" with VAT number "%(vat)s". '
                        "Please check your configuration.",
                        code=line.country_code,
                        partner=line.partner_id.name,
                        vat=line.partner_id.vat,
                    )
                )
