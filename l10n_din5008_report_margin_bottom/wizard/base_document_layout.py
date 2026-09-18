# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    l10n_din5008_margin_bottom = fields.Integer(
        related="company_id.l10n_din5008_margin_bottom",
        readonly=False,
        help=(
            "Bottom margin in millimeters for DIN 5008 PDF reports. "
            "The configured margin is not reflected in the document layout "
            "wizard preview. Always use the generated PDF report as the "
            "reference for the final result."
        ),
    )
