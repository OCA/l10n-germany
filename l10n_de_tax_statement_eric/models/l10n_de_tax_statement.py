# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
from functools import partial

from lxml import etree
from markupsafe import Markup
from psycopg2 import errors

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL, config

from odoo.addons.l10n_de_tax_statement.tools.elster_xml import add_element

from ..tools.eric import (
    ERIC_DRUCKE,
    ERIC_SENDE,
    ERIC_VALIDIERE,
    Eric,
    EricError,
)

_logger = logging.getLogger(__name__)

ELSTER_NAMESPACE = "http://www.elster.de/elsterxml/schema/v11"
# Testfall, der sofort nach Eingang in dem ELSTER-Annahmeserver gelöscht wird
TESTMERKER = "700000004"
# The server options and environment variables which point to ERiC
LIBRARY_OPTION = "l10n_de_eric_library"
LOG_PATH_OPTION = "l10n_de_eric_log_path"


class L10nDeTaxStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    eric_transfer_ticket = fields.Char(
        "ELSTER Transfer Ticket",
        copy=False,
        readonly=True,
        help="The ticket ELSTER returned for the transmission of the statement",
    )
    eric_protocol_id = fields.Many2one(
        "ir.attachment",
        string="ELSTER Transmission Protocol",
        copy=False,
        readonly=True,
        help="The protocol ERiC printed for the transmission of the statement",
    )
    eric_notes = fields.Text(
        "ELSTER Notes",
        copy=False,
        readonly=True,
        help="The notes of ERiC and ELSTER on the transmission of the statement",
    )
    is_eric_used = fields.Boolean(
        "ERiC Used",
        compute="_compute_is_eric_used",
        help="ERiC is configured on the server and sends the statements",
    )

    def _compute_is_eric_used(self):
        self.is_eric_used = self._use_eric()

    def _get_eric_library(self):
        """Return the path of ERiC as configured on the server, never in the
        database: it points to a library which runs in the Odoo process"""
        return config.get(LIBRARY_OPTION) or os.environ.get(LIBRARY_OPTION.upper())

    def _use_eric(self):
        """Whether ERiC sends the statements: it is configured on the server"""
        return bool(self._get_eric_library())

    def _is_eric_test(self):
        """Whether ERiC sends the statement as a test, which doesn't declare
        it"""
        return self._use_eric() and self.company_id.l10n_de_eric_test

    def _check_eric_configured(self):
        if not self._use_eric():
            raise UserError(
                self.env._(
                    "ERiC isn't configured: set %(option)s in the configuration "
                    "file of the Odoo server to the path of libericapi.so.",
                    option=LIBRARY_OPTION,
                )
            )

    def _get_eric(self):
        self._check_eric_configured()
        library = self._get_eric_library()
        log_path = config.get(LOG_PATH_OPTION) or os.environ.get(
            LOG_PATH_OPTION.upper()
        )
        return Eric(library, log_path)

    def _get_eric_datenart_version(self):
        return f"UStVA_{self.year}"

    def _get_eric_country_name(self):
        """Return the country of the company in German, like the examples of
        ELSTER, whatever the language of the user. Without German loaded, it
        is the English name."""
        self.ensure_one()
        lang = self.env["res.lang"]._get_code("de_DE") or "en_US"
        return self.company_id.country_id.with_context(lang=lang).name or ""

    def _get_eric_envelope(self, verfahren, datenart, empfaenger, nutzdaten):
        """Return the ELSTER XML for ERiC: ``nutzdaten`` (an element) in the
        envelope of a transmission to ``empfaenger``, a tuple of the id and
        the content of the Empfaenger of the NutzdatenHeader"""
        self.ensure_one()
        hersteller_id = self._get_elster_hersteller_id()
        datenlieferant = self._get_elster_datenlieferant()

        sub = partial(add_element, ELSTER_NAMESPACE)

        elster = etree.Element(
            f"{{{ELSTER_NAMESPACE}}}Elster", nsmap={None: ELSTER_NAMESPACE}
        )
        transfer_header = sub(elster, "TransferHeader", version="11")
        sub(transfer_header, "Verfahren", verfahren)
        sub(transfer_header, "DatenArt", datenart)
        sub(transfer_header, "Vorgang", "send-Auth")
        if self.company_id.l10n_de_eric_test:
            sub(transfer_header, "Testmerker", TESTMERKER)
        sub(transfer_header, "HerstellerID", hersteller_id)
        sub(
            transfer_header,
            "DatenLieferant",
            # name;street;house number;its addition;address addition;zip;
            # city;country;phone;email, like the examples of the schema: a ";"
            # of a value would shift the fields after it
            ";".join(
                (value or "").replace(";", ",")
                for value in [
                    datenlieferant["Name"],
                    datenlieferant["Strasse"],
                    "",
                    "",
                    "",
                    datenlieferant["PLZ"],
                    datenlieferant["Ort"],
                    self._get_eric_country_name(),
                    datenlieferant.get("Telefon", ""),
                    datenlieferant.get("Email", ""),
                ]
            )[:256],
        )
        datei = sub(transfer_header, "Datei")
        sub(datei, "Verschluesselung", "CMSEncryptedData")
        sub(datei, "Kompression", "GZIP")

        nutzdatenblock = sub(sub(elster, "DatenTeil"), "Nutzdatenblock")
        nutzdaten_header = sub(nutzdatenblock, "NutzdatenHeader", version="11")
        sub(nutzdaten_header, "NutzdatenTicket", str(self.id))
        empfaenger_id, empfaenger_text = empfaenger
        sub(nutzdaten_header, "Empfaenger", empfaenger_text, id=empfaenger_id)
        hersteller = sub(nutzdaten_header, "Hersteller")
        sub(hersteller, "ProduktName", "Odoo")
        sub(hersteller, "ProduktVersion", self._get_elster_product_version())
        sub(nutzdatenblock, "Nutzdaten")
        # ERiC reads the Nutzdaten on their own: their root element must
        # declare its namespace, even if it is the one of the envelope, which
        # lxml would drop as redundant
        return etree.tostring(elster, xml_declaration=True, encoding="UTF-8").replace(
            b"<Nutzdaten/>",
            b"<Nutzdaten>"
            + etree.tostring(nutzdaten, encoding="UTF-8", xml_declaration=False)
            + b"</Nutzdaten>",
        )

    def _get_eric_xml(self):
        """Return the statement as ELSTER XML for ERiC: the Anmeldungssteuern of
        the XML export in the envelope of a transmission"""
        self.ensure_one()
        steuernummer = self._get_elster_steuernummer()
        return self._get_eric_envelope(
            "ElsterAnmeldung",
            "UStVA",
            # the Bundesfinanzamtsnummer are the first four digits of the tax
            # number
            ("F", steuernummer[:4]),
            etree.fromstring(self._get_elster_xml()),
        )

    def _get_eric_messages(self, result):
        """Return the texts of the errors and notes of ERiC and ELSTER, without
        the confirmations of ELSTER: their code is 0"""
        texts = []
        for xml in (result.response, result.server_response):
            if not xml:
                continue
            try:
                root = etree.fromstring(xml.encode())
            except etree.XMLSyntaxError:
                continue
            texts += [
                text.strip()
                for text in root.xpath(
                    "//*[local-name()='Text']"
                    "[not(../*[local-name()='Code'] = '0')]/text()"
                )
                if text.strip()
            ]
        return texts

    def _eric_process(self, xml, datenart_version, flags, certificate=None, pin=None):
        self.ensure_one()
        try:
            with self._get_eric().session() as eric:
                result = eric.process(
                    xml,
                    datenart_version,
                    flags,
                    certificate=certificate,
                    pin=pin,
                )
        except EricError as error:
            raise UserError(
                self.env._("ERiC failed: %(error)s", error=error.message)
            ) from error
        if not result.ok:
            raise UserError(
                "\n".join(
                    [self.env._("ELSTER rejected the statement: %s", result.message)]
                    + self._get_eric_messages(result)
                )
            )
        return result

    def _eric_attach_pdf(self, result, name):
        """Attach the PDF ERiC printed: one, as the statement is sent in one
        Nutzdatenblock. Nothing if ERiC printed none."""
        pdf = next(iter(result.pdfs.values()), None)
        if not pdf:
            return self.env["ir.attachment"]
        return self.env["ir.attachment"].create(
            {
                "name": f"{name}.pdf",
                "raw": pdf,
                "mimetype": "application/pdf",
                "res_model": self._name,
                "res_id": self.id,
            }
        )

    def _eric_lock(self):
        """Lock the statements before they are sent: no other transaction can
        change them until the sending is committed. Otherwise a serialization
        failure after the sending rolls it back, and Odoo retries it: ELSTER
        receives the declaration twice."""
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(
                    SQL(
                        "SELECT id FROM %s WHERE id IN %s FOR UPDATE NOWAIT",
                        SQL.identifier(self._table),
                        tuple(self.ids),
                    )
                )
        except errors.LockNotAvailable:
            raise UserError(
                self.env._(
                    "Another user is changing the statement, try again in a moment."
                )
            ) from None

    def _eric_transmit(self, xml, datenart_version, certificate, pin, name):
        """Send ``xml`` to ELSTER and return the transfer ticket, the attached
        transmission protocol and the notes of ERiC and ELSTER. ELSTER has
        the declaration once ERiC sent it, which can't be undone: a failure
        afterwards becomes a note, the caller goes on as sent."""
        self._eric_lock()
        result = self._eric_process(
            xml,
            datenart_version,
            ERIC_VALIDIERE | ERIC_SENDE | ERIC_DRUCKE,
            certificate=certificate,
            pin=pin,
        )
        try:
            with self.env.cr.savepoint():
                return self._eric_read_transmission(result, name)
        except Exception as error:
            _logger.exception("ELSTER received %s, its answer failed", name)
            return (
                False,
                self.env["ir.attachment"],
                [
                    self.env._(
                        "ELSTER received %(name)s, but its answer couldn't be "
                        "read: %(error)s Check the transmission in Mein ELSTER.",
                        name=name,
                        error=error.args[0] if error.args else repr(error),
                    )
                ],
            )

    def _eric_read_transmission(self, result, name):
        """Return the transfer ticket, the attached transmission protocol and
        the notes of the ``result`` of a transmission"""
        # ERiC 44 returns the ticket only in the answer of the server
        tickets = (
            etree.fromstring(result.server_response.encode()).xpath(
                "//*[local-name()='TransferTicket']/text()"
            )
            if result.server_response
            else []
        )
        return (
            tickets[0] if tickets else False,
            self._eric_attach_pdf(result, f"{name}_Protokoll"),
            self._get_eric_messages(result),
        )

    def _get_eric_transmission_body(self, title, ticket, notes):
        lines = [title]
        if ticket:
            lines.append(self.env._("Transfer ticket: %s", ticket))
        return Markup("<br/>").join(lines + notes)

    def _eric_post_test_transmission(self, name, ticket, protocol, notes):
        """Post a test transmission: it doesn't approve the statement"""
        self.message_post(
            body=self._get_eric_transmission_body(
                self.env._("ELSTER received %s as a test, it isn't declared.", name),
                ticket,
                notes,
            ),
            attachment_ids=protocol.ids,
        )

    def _get_eric_name(self):
        return f"UStVA_{self.year}_{self.period}"

    def _check_eric(self):
        """Let ERiC validate the statement before it is sent: the approval
        reports its errors before it asks for the certificate"""
        self._eric_process(
            self._get_eric_xml(), self._get_eric_datenart_version(), ERIC_VALIDIERE
        )

    def _check_approve(self):
        res = super()._check_approve()
        if self._use_eric():
            self._check_eric()
        return res

    def _get_eric_credentials(self):
        """Return the certificate and its PIN: given in the dialog, or else
        stored on the company. None if there are neither, or if the user
        didn't confirm the privacy notice yet: the dialog asks for it."""
        if not self.env.user.l10n_de_eric_privacy_notice_date:
            return None
        context = self.env.context
        if context.get("l10n_de_eric_certificate") and context.get("l10n_de_eric_pin"):
            return context["l10n_de_eric_certificate"], context["l10n_de_eric_pin"]
        return self.company_id._l10n_de_eric_get_stored_credentials()

    def _get_eric_send_action(self, declaration):
        """Return the dialog which asks for the certificate and its PIN"""
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n.de.tax.statement.eric.send",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_statement_id": self.id,
                "default_declaration": declaration,
            },
        }

    def action_approve(self):
        """Without the certificate the approval asks for it first: the dialog
        approves the statement again with it"""
        self.ensure_one()
        if self._use_eric() and not self._get_eric_credentials():
            self._check_approve()
            return self._get_eric_send_action("ustva")
        return super().action_approve()

    def _action_approve(self):
        """Send the statement to ELSTER before it is approved, the approval
        gets the transmission protocol. A test transmission doesn't approve
        it."""
        if not self._use_eric():
            return super()._action_approve()
        credentials = self._get_eric_credentials()
        if not credentials:
            raise UserError(self.env._("Upload the certificate file of Mein ELSTER."))
        ticket, protocol, notes = self._eric_transmit(
            self._get_eric_xml(),
            self._get_eric_datenart_version(),
            *credentials,
            self._get_eric_name(),
        )
        if self._is_eric_test():
            self._eric_post_test_transmission(
                self._get_eric_name(), ticket, protocol, notes
            )
            return
        self.write(
            {
                "eric_transfer_ticket": ticket,
                "eric_protocol_id": protocol.id,
                "eric_notes": "\n".join(notes),
            }
        )
        return super()._action_approve()

    def _post_approve_message(self):
        """A test transmission doesn't approve the statement: its message is
        posted already. A sent statement stays approved if the message fails,
        the ticket, protocol and notes are kept on it."""
        if self._is_eric_test():
            return
        if not self._use_eric():
            return super()._post_approve_message()
        try:
            with self.env.cr.savepoint():
                return super()._post_approve_message()
        except Exception:
            _logger.exception("The message of the approved %s failed", self)

    def _get_approve_message(self):
        if not self._use_eric():
            return super()._get_approve_message()
        return self._get_eric_transmission_body(
            self.env._("The statement is approved and sent to ELSTER."),
            self.eric_transfer_ticket,
            (self.eric_notes or "").splitlines(),
        )

    def _get_approve_attachments(self):
        """The transmission protocol: ERiC sent the statement, there is
        nothing to upload"""
        if not self._use_eric():
            return super()._get_approve_attachments()
        return self.eric_protocol_id
