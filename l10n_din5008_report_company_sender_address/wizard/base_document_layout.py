# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    l10n_din5008_country_indicator = fields.Selection(
        related="company_id.l10n_din5008_country_indicator",
        readonly=False,
        help="Determines if and how the country is indicated in the "
        "company sender address.",
    )

    l10n_din5008_address_separator = fields.Selection(
        related="company_id.l10n_din5008_address_separator",
        readonly=False,
        help="Defines the separator used between address components.",
    )

    l10n_din5008_sender_font_factor = fields.Float(
        related="company_id.l10n_din5008_sender_font_factor",
        readonly=False,
        help="Scale factor for the company sender address font size.",
    )

    @api.onchange(
        "l10n_din5008_country_indicator",
        "l10n_din5008_address_separator",
        "l10n_din5008_sender_font_factor",
    )
    def _onchange_din5008_report_company_sender_address(self):
        for wizard in self:
            wizard._compute_preview()
