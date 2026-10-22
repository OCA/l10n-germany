# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_din5008_optional_field(self, field_name):
        self.ensure_one()

        if field_name not in self._fields:
            return False

        return getattr(self, field_name, False)
