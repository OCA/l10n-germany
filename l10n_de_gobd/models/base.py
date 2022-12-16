# Copyright 2022 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def _is_gobd_restricted(self):
        """
        Return True if one of the current records neds to be immutable according
        to the GoBD
        """
        return False
