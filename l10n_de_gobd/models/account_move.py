# Copyright 2022 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _is_gobd_restricted(self):
        """Posted moves are restricted"""
        return any(this.state == "posted" for this in self)
