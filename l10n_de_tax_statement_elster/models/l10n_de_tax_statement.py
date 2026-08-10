# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VatStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    def action_generate_elster_xml(self):
        self.ensure_one()

        if self.state == "draft":
            raise UserError(
                _(
                    "Die Umsatzsteuer-Voranmeldung muss berechnet "
                    "und gebucht sein, bevor sie exportiert werden kann."
                )
            )

        if self.version != "2026":
            raise UserError(
                _("Der ELSTER Export unterstützt nur " "die UStVA Version 2026.")
            )

        return {
            "type": "ir.actions.act_url",
            "url": f"/l10n_de_tax_statement_elster/{self.id}/download",
            "target": "self",
        }
