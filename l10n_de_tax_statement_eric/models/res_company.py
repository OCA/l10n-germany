# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models

# The notice the license of ERiC requires to show before the software is used
PRIVACY_NOTICE = (
    "Mit dieser Software werden personenbezogene Daten im Sinne des Art. 4 Nr. 1 "
    "Datenschutzgrundverordnung (DSGVO) und Art. 9 Abs. 1 DSGVO zum Zwecke der "
    "Verarbeitung erhoben. Neben den reinen Daten, die zur Steuerveranlagung "
    "benötigt werden, erhebt die Software Daten über die Art des Betriebssystems "
    "des Nutzers und übermittelt diese an die Finanzverwaltung. Diese Daten werden "
    "benötigt, um die ordnungsgemäße Verarbeitung der Daten sicherzustellen und "
    "Fehlern im Verarbeitungsprozess vorzubeugen. Die Nutzung der Daten erfolgt im "
    "Rahmen des Art. 6 Abs. 1 UAbs. 1 Buchst. e i.V.m. Abs. 3 UAbs. 1 Buchst. b "
    "DSGVO i.V.m. bundes- bzw. landesgesetzlicher Steuergesetze durch die "
    "Finanzverwaltung und nur für den genannten Zweck."
)


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_de_eric_test = fields.Boolean(
        "ELSTER Test Transmission",
        help="Send the statements with the Testmerker 700000004: ELSTER "
        "deletes them right after their receipt, they aren't declared.",
    )
    l10n_de_eric_store_certificate = fields.Boolean(
        "Store the ELSTER Certificate",
        help="Keep the certificate file and its PIN in the database: the "
        "approval of a statement sends it right away, without asking for them.",
    )
    l10n_de_eric_certificate = fields.Binary(
        "ELSTER Certificate",
        attachment=True,
        copy=False,
        groups="base.group_system",
        help="The certificate file (.pfx) of Mein ELSTER",
    )
    l10n_de_eric_certificate_name = fields.Char(
        "ELSTER Certificate Name", copy=False, groups="base.group_system"
    )
    l10n_de_eric_pin = fields.Char(
        "ELSTER Certificate PIN", copy=False, groups="base.group_system"
    )

    def _l10n_de_eric_get_stored_credentials(self):
        """Return the stored certificate and its PIN, None unless both are
        stored"""
        self.ensure_one()
        company = self.sudo()
        if not (
            company.l10n_de_eric_store_certificate
            and company.l10n_de_eric_certificate
            and company.l10n_de_eric_pin
        ):
            return None
        return (
            base64.b64decode(company.l10n_de_eric_certificate),
            company.l10n_de_eric_pin,
        )

    def write(self, vals):
        if vals.get("l10n_de_eric_store_certificate") is False:
            vals.update(
                {
                    "l10n_de_eric_certificate": False,
                    "l10n_de_eric_certificate_name": False,
                    "l10n_de_eric_pin": False,
                }
            )
        return super().write(vals)
