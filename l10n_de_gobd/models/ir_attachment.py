# Copyright 2022 Hunki Enterprises BV (https://hunki-enterprises.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, exceptions, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def check(self, mode, values=None):
        """Restrict attachments of account.move according to GoBD"""
        if mode in ("unlink", "write"):
            for this in self:
                if this.type != "binary":
                    continue
                if (
                    this.res_model in self.env
                    and self.env[this.res_model]
                    .browse(this.res_id)
                    ._is_gobd_restricted()
                ):
                    raise exceptions.AccessError(
                        _("You are not allowed to delete or modify this attachment: %s")
                        % this.res_name
                    )
        return super().check(mode, values=values)
