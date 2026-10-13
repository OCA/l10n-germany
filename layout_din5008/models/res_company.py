# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company", "layout.din5008.mixin"]

    # The DIN 5008 settings are stored in report_layout_config (see
    # report_layout_config_mixin.py); only the formatted sender line is a
    # field, so that it can be used as placeholder in the layout texts.
    layout_din5008_sender_line_text = fields.Char(
        string="DIN 5008 Sender Line Text",
        compute="_compute_layout_din5008_sender_line_text",
        store=True,
        help="Name and address of the company formatted as a single line with "
        "the configured separator and country indicator. Available as "
        "placeholder in the address, tagline and footer texts of the document "
        "layout; insert it into the address to print it as sender line.",
    )

    @api.model
    def mail_allowed_qweb_expressions(self):
        return super().mail_allowed_qweb_expressions() + (
            "object.layout_din5008_sender_line_text",
        )

    @api.depends(
        "name",
        "partner_id.street",
        "partner_id.street2",
        "partner_id.zip",
        "partner_id.city",
        "partner_id.country_id",
        "report_layout_config",
    )
    def _compute_layout_din5008_sender_line_text(self):
        for company in self:
            company.layout_din5008_sender_line_text = (
                company._layout_din5008_format_sender_line()
            )
