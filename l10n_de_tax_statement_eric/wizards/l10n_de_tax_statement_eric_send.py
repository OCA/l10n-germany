# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

from ..models.res_company import PRIVACY_NOTICE


class L10nDeTaxStatementEricSend(models.TransientModel):
    _name = "l10n.de.tax.statement.eric.send"
    _description = "Send a German VAT Statement to ELSTER"

    statement_id = fields.Many2one(
        "l10n.de.tax.statement", required=True, ondelete="cascade"
    )
    declaration = fields.Selection(
        [("ustva", "Umsatzsteuer-Voranmeldung")], required=True, default="ustva"
    )
    is_test = fields.Boolean(related="statement_id.company_id.l10n_de_eric_test")
    # The certificate and its PIN are only kept until the transmission, see
    # _clear_secrets(); attachment=False keeps the file out of the filestore
    certificate = fields.Binary("ELSTER Certificate", attachment=False)
    certificate_name = fields.Char()
    pin = fields.Char("PIN")
    is_stored = fields.Boolean(compute="_compute_is_stored")
    privacy_notice = fields.Text(default=PRIVACY_NOTICE, readonly=True)
    # the license of ERiC requires the notice once per user, before the
    # first transmission
    privacy_notice_confirmed = fields.Boolean(
        default=lambda self: bool(self.env.user.l10n_de_eric_privacy_notice_date),
        readonly=True,
    )
    privacy_notice_read = fields.Boolean("I have read the privacy notice")

    @api.depends("statement_id")
    def _compute_is_stored(self):
        """The certificate and its PIN are stored on the company: the dialog
        only asks for the privacy notice"""
        for wizard in self:
            wizard.is_stored = bool(
                wizard.statement_id.company_id._l10n_de_eric_get_stored_credentials()
            )

    def _get_certificate(self):
        if not self.certificate:
            raise UserError(self.env._("Upload the certificate file of Mein ELSTER."))
        return base64.b64decode(self.certificate)

    def _get_clear_secrets_query(self):
        return SQL(
            "UPDATE %s SET certificate = NULL, pin = NULL WHERE id IN %s",
            SQL.identifier(self._table),
            tuple(self.ids),
        )

    def _clear_secrets(self):
        """Remove the certificate and the PIN from the database with the
        transaction of the transmission"""
        self.env.cr.execute(self._get_clear_secrets_query())
        self.invalidate_recordset(["certificate", "pin"])

    def _clear_secrets_after_rollback(self):
        """Remove the certificate and the PIN from the database when the
        transaction of the transmission fails: in a cursor of its own, as the
        failed one is rolled back. Only then, as the cursor commits at once:
        an update of the wizard in both transactions conflicts. A wizard the
        other cursor doesn't see isn't committed yet, the current transaction
        clears it without a conflict."""
        query = self._get_clear_secrets_query()
        with self.env.registry.cursor() as cr:
            cr.execute(query)
            cleared = cr.rowcount
        if cleared < len(self):
            self.env.cr.execute(query)
        self.invalidate_recordset(["certificate", "pin"])

    def _send(self, statement):
        """Send the declaration of ``statement``, which has the certificate
        and its PIN in its context, extended by the modules which add
        declarations"""
        if self.declaration == "ustva":
            return statement.action_approve()
        raise UserError(self.env._("Unknown declaration %s", self.declaration))

    def action_send(self):
        self.ensure_one()
        try:
            if not (self.privacy_notice_confirmed or self.privacy_notice_read):
                raise UserError(self.env._("Please read the privacy notice first."))
            statement = self.statement_id
            if not (self.is_stored and not self.certificate):
                if not self.pin:
                    raise UserError(self.env._("Enter the PIN of the certificate."))
                statement = statement.with_context(
                    l10n_de_eric_certificate=self._get_certificate(),
                    l10n_de_eric_pin=self.pin,
                )
            self.env.user._l10n_de_eric_confirm_privacy_notice()
            self._send(statement)
        except Exception:
            self._clear_secrets_after_rollback()
            raise
        self._clear_secrets()
        return {"type": "ir.actions.act_window_close"}
