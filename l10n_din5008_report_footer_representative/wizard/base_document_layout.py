# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    representatives = fields.One2many(
        related="company_id.representatives",
        readonly=True,
        help="Representatives of the current company",
    )

    din_5008_show_representatives = fields.Boolean(
        related="company_id.din_5008_show_representatives", readonly=False
    )

    def get_representatives(self):
        return self.company_id.get_representatives()

    @api.onchange(
        "din_5008_show_representatives",
    )
    def _onchange_din5008_report_show_representatives(self):
        for wizard in self:
            wizard._compute_preview()
