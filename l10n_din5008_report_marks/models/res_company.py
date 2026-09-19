# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_din5008_hole_marker = fields.Boolean(
        string="DIN Punch/Hole Marker", default=True, store=True
    )
    l10n_din5008_fold_marker = fields.Boolean(
        string="DIN Fold Marker", default=True, store=True
    )
