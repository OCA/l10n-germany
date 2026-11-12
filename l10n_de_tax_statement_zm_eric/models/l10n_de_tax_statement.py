# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re
from functools import partial

from lxml import etree
from markupsafe import Markup

from odoo import fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_de_tax_statement.tools.elster_xml import add_element
from odoo.addons.l10n_de_tax_statement_eric.models.l10n_de_tax_statement import (
    ELSTER_NAMESPACE,
)
from odoo.addons.l10n_de_tax_statement_eric.tools.eric import ERIC_VALIDIERE

_logger = logging.getLogger(__name__)

# The Datenartversion of ERiC for the ZM, see Datenartversionmatrix.ods
ZM_DATENART_VERSION = "ZMDO"
# The version of the schema zm_000005.xsd
ZM_VERSION = "000005"
# The BZSt receives the ZM: Empfaenger "BF" with the id "L"
ZM_EMPFAENGER = ("L", "BF")


class L10nDeTaxStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    zm_is_sent = fields.Boolean("ZM Sent to the BZSt", copy=False, readonly=True)
    zm_eric_transfer_ticket = fields.Char(
        "ZM Transfer Ticket",
        copy=False,
        readonly=True,
        help="The ticket ELSTER returned for the transmission of the ZM",
    )
    zm_eric_protocol_id = fields.Many2one(
        "ir.attachment",
        "ZM Transmission Protocol",
        copy=False,
        readonly=True,
        help="The protocol ERiC printed for the transmission of the ZM",
    )
    zm_eric_notes = fields.Text(
        "ZM Notes",
        copy=False,
        readonly=True,
        help="The notes of ERiC and ELSTER on the transmission of the ZM",
    )
    zm_eric_error = fields.Char(
        "ZM Error",
        copy=False,
        readonly=True,
        help="Why the ZM failed when the statement was sent",
    )

    def _get_zm_quart(self):
        """Return the Meldezeitraum of the ZM: 1 to 4 for the quarters, 21 to
        32 for the months"""
        period = int(self.period)
        return period - 40 if period > 40 else 20 + period

    def _get_zm_knri(self):
        vat = (self.company_id.vat or "").replace(" ", "").upper()
        if not re.fullmatch(r"DE[0-9]{9}", vat):
            raise UserError(
                self.env._(
                    "Set the German VAT number (DE and 9 digits) of the company "
                    "%(company)s first, the ZM requires it.",
                    company=self.company_id.name,
                )
            )
        return vat

    def _get_zm_eric_xml(self, rows=None):
        """Return the ZM as ELSTER XML for ERiC, schema zm_000005.xsd, of
        ``rows``: the rows of the ZM by default"""
        self.ensure_one()
        if rows is None:
            rows = self._get_zm_rows()
        if not rows:
            raise UserError(self.env._("The statement has no ZM lines to send."))
        datenlieferant = self._get_elster_datenlieferant()

        sub = partial(add_element, ELSTER_NAMESPACE)

        zm = etree.Element(
            f"{{{ELSTER_NAMESPACE}}}zm",
            {"version": ZM_VERSION},
            nsmap={None: ELSTER_NAMESPACE},
        )
        unternehmer = sub(zm, "unternehmer")
        sub(unternehmer, "knri", self._get_zm_knri())
        # the BZSt-Nummer isn't needed any more: ERiC takes the letter N and
        # the number 1111111
        zulass_nr = sub(unternehmer, "zulassNr")
        sub(zulass_nr, "zulnr1", "N")
        sub(zulass_nr, "zulnr2", "1111111")
        anschrift = sub(unternehmer, "anschrift")
        sub(anschrift, "name", (self.company_id.partner_id.name or "")[:100])
        sub(anschrift, "strasse", datenlieferant["Strasse"])
        sub(anschrift, "plz", datenlieferant["PLZ"])
        sub(anschrift, "ort", datenlieferant["Ort"])
        sub(anschrift, "staat", self.company_id.country_id.code or "DE")
        phone = re.sub(r"[^0-9+\-/() ]", "", datenlieferant.get("Telefon", ""))
        if phone.strip():
            sub(anschrift, "telefon", phone.strip()[:20])
        zm_zeilen = sub(
            unternehmer,
            "zm-zeilen",
            # 1 for euro, 10 for the first ZM of the period, 11 for a corrected
            waehrung="1",
            meldeart="11" if self.is_corrected else "10",
        )
        sub(zm_zeilen, "anzeige", "false")
        sub(zm_zeilen, "widerruf", "false")
        mzr = sub(zm_zeilen, "mzr")
        sub(mzr, "quart", str(self._get_zm_quart()))
        sub(mzr, "jahr", str(self.year))
        for vat, amount, umsatzart in rows:
            zeile = sub(zm_zeilen, "zeile", umsatzart=umsatzart)
            sub(zeile, "knre", vat)
            sub(zeile, "betrag", str(amount))
        return self._get_eric_envelope("ElsterExtern", "ZMDO", ZM_EMPFAENGER, zm)

    def _get_zm_eric_name(self):
        return f"ZM_{self.year}_{self.period}"

    def _get_zm_eric_xml_to_send(self):
        """Return the ZM to send along with the statement, False without ZM"""
        rows = self._get_zm_rows()
        if not rows:
            return False
        return self._get_zm_eric_xml(rows)

    def _check_zm_eric(self):
        """Let ERiC validate the ZM: the statement is sent before it, which
        can't be undone"""
        zm_xml = self._get_zm_eric_xml_to_send()
        if zm_xml:
            self._eric_process(zm_xml, ZM_DATENART_VERSION, ERIC_VALIDIERE)

    def _check_approve(self):
        res = super()._check_approve()
        if self._use_eric():
            self._check_zm_eric()
        return res

    def _action_approve(self):
        """Send the ZM along with the statement: the approval reports it, a
        test transmission posts it on its own"""
        zm_xml = self._use_eric() and self._get_zm_eric_xml_to_send()
        if not zm_xml:
            return super()._action_approve()
        res = super()._action_approve()
        try:
            with self.env.cr.savepoint():
                ticket, protocol, notes = self._eric_send_zm(zm_xml)
        except Exception as error:
            # the statement is declared and stays so, send the ZM again
            if not isinstance(error, UserError):
                _logger.exception("The ZM of %s failed", self)
            text = error.args[0] if error.args else repr(error)
            if self._is_eric_test():
                self.message_post(body=self.env._("The ZM failed: %s", text))
            else:
                self.zm_eric_error = text
            return res
        if self._is_eric_test():
            self._eric_post_test_transmission(
                self._get_zm_eric_name(), ticket, protocol, notes
            )
        return res

    def _get_approve_message(self):
        message = super()._get_approve_message()
        if not self._use_eric():
            return message
        if self.zm_is_sent:
            zm_message = self._get_eric_transmission_body(
                self.env._("The ZM is sent to the BZSt."),
                self.zm_eric_transfer_ticket,
                (self.zm_eric_notes or "").splitlines(),
            )
        elif self.zm_eric_error:
            zm_message = self.env._(
                "The ZM isn't sent: %(error)s Send it again with Send ZM to the "
                "BZSt.",
                error=self.zm_eric_error,
            )
        else:
            return message
        return Markup("<br/>").join([message, zm_message])

    def _get_approve_attachments(self):
        attachments = super()._get_approve_attachments()
        if self._use_eric():
            attachments |= self.zm_eric_protocol_id
        return attachments

    def _eric_send_zm(self, zm_xml=None):
        """Send the ZM to the BZSt, keep its ticket and its protocol and return
        them with the notes of ERiC and ELSTER"""
        self.ensure_one()
        if self.zm_is_sent:
            raise UserError(self.env._("The ZM of the statement was sent already."))
        credentials = self._get_eric_credentials()
        if not credentials:
            raise UserError(self.env._("Upload the certificate file of Mein ELSTER."))
        ticket, protocol, notes = self._eric_transmit(
            zm_xml or self._get_zm_eric_xml(),
            ZM_DATENART_VERSION,
            *credentials,
            self._get_zm_eric_name(),
        )
        if not self._is_eric_test():
            self.write(
                {
                    "zm_is_sent": True,
                    "zm_eric_transfer_ticket": ticket,
                    "zm_eric_protocol_id": protocol.id,
                    "zm_eric_notes": "\n".join(notes),
                    "zm_eric_error": False,
                }
            )
        return ticket, protocol, notes

    def action_zm_eric_send(self):
        """Send the ZM again, if it failed when the statement was approved.
        Without the certificate it asks for it first."""
        self.ensure_one()
        self._check_approve_access()
        # without ERiC the ZM is uploaded with the files of the approval, it
        # can't be sent again
        self._check_eric_configured()
        if self.state != "approved":
            raise UserError(
                self.env._("Only the ZM of an approved statement can be sent again.")
            )
        if self._is_eric_test():
            raise UserError(
                self.env._(
                    "Switch off the test mode of ERiC to send the ZM of an approved "
                    "statement."
                )
            )
        if not self._get_eric_credentials():
            return self._get_eric_send_action("zm")
        ticket, protocol, notes = self._eric_send_zm()
        self.message_post(
            body=self._get_eric_transmission_body(
                self.env._("The ZM is sent to the BZSt."), ticket, notes
            ),
            attachment_ids=protocol.ids,
        )
        return True
