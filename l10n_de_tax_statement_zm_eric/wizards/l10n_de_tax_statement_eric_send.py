# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class L10nDeTaxStatementEricSend(models.TransientModel):
    _inherit = "l10n.de.tax.statement.eric.send"

    declaration = fields.Selection(
        selection_add=[("zm", "Zusammenfassende Meldung")],
        ondelete={"zm": "cascade"},
    )

    def _send(self, statement):
        if self.declaration == "zm":
            return statement.action_zm_eric_send()
        return super()._send(statement)
