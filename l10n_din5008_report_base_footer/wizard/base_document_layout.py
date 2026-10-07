# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    def _get_din5008_optional_field(self, field_name):
        self.ensure_one()

        return self.company_id._get_din5008_optional_field(field_name)
