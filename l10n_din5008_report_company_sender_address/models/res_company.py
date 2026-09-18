# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_din5008_country_indicator = fields.Selection(
        [("none", "No indication"), ("code", "Country Code"), ("name", "Country Name")],
        string="Country indicator",
        required=True,
        default="none",
        store=True,
    )

    l10n_din5008_address_separator = fields.Selection(
        [
            ("pipe", "Pipe (|)"),
            ("dot", "Dot (•)"),
        ],
        string="Address Separator",
        default="pipe",
        required=True,
        store=True,
    )

    l10n_din5008_sender_font_factor = fields.Float(
        string="Font Scale Company Sender Address",
        default=1.0,
        digits=(1, 2),
        help="Scale factor for sender address font size.",
        store=True,
    )

    @api.constrains("l10n_din5008_sender_font_factor")
    def _check_l10n_din5008_sender_font_factor(self):
        for company in self:
            if not 0.5 <= company.l10n_din5008_sender_font_factor <= 1.5:
                raise ValidationError(
                    self.env._(
                        "The company sender font scale must be between 0.5 and 1.5."
                    )
                )
