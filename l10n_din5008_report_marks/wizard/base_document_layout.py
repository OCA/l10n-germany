# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    l10n_din5008_hole_marker = fields.Boolean(
        related="company_id.l10n_din5008_hole_marker",
        readonly=False,
        help="Indicates whether the DIN 5008 punch/hole marker is displayed.",
    )
    l10n_din5008_fold_marker = fields.Boolean(
        related="company_id.l10n_din5008_fold_marker",
        readonly=False,
        help="Indicates whether the DIN 5008 fold markers are displayed.",
    )

    @api.onchange(
        "paperformat_id",
        "l10n_din5008_hole_marker",
        "l10n_din5008_fold_marker",
    )
    def _onchange_din5008_report_marks(self):
        self._compute_preview()
