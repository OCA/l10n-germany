# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    l10n_de_eric_privacy_notice_date = fields.Datetime(
        "ELSTER Privacy Notice Confirmed",
        copy=False,
        readonly=True,
        help="When the user confirmed the privacy notice of the tax "
        "administration: the license of ERiC requires it once, before the "
        "user sends with it",
    )

    def _l10n_de_eric_confirm_privacy_notice(self):
        """Record the confirmation of the privacy notice, once per user: as
        superuser, the users can't write their own record"""
        self.sudo().filtered(
            lambda user: not user.l10n_de_eric_privacy_notice_date
        ).l10n_de_eric_privacy_notice_date = fields.Datetime.now()
