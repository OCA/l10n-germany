# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_de_datev_export_identifier_customer = fields.Char("DATEV number (customer)")
    l10n_de_datev_export_identifier_supplier = fields.Char("DATEV number (supplier)")
    l10n_de_datev_export_show = fields.Boolean(
        compute="_compute_l10n_de_datev_export_show"
    )

    def _compute_l10n_de_datev_export_show(self):
        """Determine if we show the identifiers in the form"""
        for this in self:
            this.l10n_de_datev_export_show = (
                self.env.company.datev_partner_numbering == "sequence"
            )

    def action_l10n_de_datev_export_identifier_customer(self):
        """Generate number if not set"""
        self.l10n_de_datev_export_identifier_customer = (
            self.l10n_de_datev_export_identifier_customer
            or self.env.company.datev_customer_sequence_id._next()
        )

    def action_l10n_de_datev_export_identifier_supplier(self):
        """Generate number if not set"""
        self.l10n_de_datev_export_identifier_supplier = (
            self.l10n_de_datev_export_identifier_supplier
            or self.env.company.datev_supplier_sequence_id._next()
        )
