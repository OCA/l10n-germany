# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_din5008_margin_bottom = fields.Integer(
        string="Margin Bottom (mm)",
        default=28,
        help="Bottom margin in millimeters for DIN 5008 PDF reports.",
    )

    @api.constrains("l10n_din5008_margin_bottom")
    def _check_l10n_din5008_margin_bottom(self):
        for company in self:
            if not 5 <= company.l10n_din5008_margin_bottom <= 60:
                raise ValidationError(
                    self.env._(
                        "The bottom DIN 5008 margin must be between 5 and 60 mm."
                    )
                )
