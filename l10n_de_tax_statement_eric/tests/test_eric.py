# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from lxml import etree
from psycopg2 import errors

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import config, mute_logger

from odoo.addons.l10n_de_tax_statement.models.elster_config import (
    HERSTELLER_ID_PARAM,
)

from ..tools.eric import ERIC_SENDE
from .common import HINT_RESPONSE, EricFakeCase

ELSTER = "{http://www.elster.de/elsterxml/schema/v11}"
USTVA = "{http://finkonsens.de/elster/elsteranmeldung/ustva/v2025}"
NO_TICKET_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<Elster xmlns="http://www.elster.de/elsterxml/schema/v11">
  <TransferHeader version="11"/>
</Elster>"""


@tagged("-at_install", "post_install")
class TestEric(EricFakeCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test company",
                "country_id": cls.env.ref("base.de").id,
                "state_id": cls.env.ref("base.state_de_bw").id,
                "currency_id": cls.env.ref("base.EUR").id,
                "street": "Testgasse 13",
                "zip": "08151",
                "city": "Musterstadt",
            }
        )
        cls.company.l10n_de_stnr = "93815/08152"
        cls.env.company = cls.company
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "12345")
        cls.statement = cls.env["l10n.de.tax.statement"].create(
            {"year": 2025, "period": "41"}
        )
        cls.statement.action_update()

    def test_eric_xml(self):
        root = etree.fromstring(self.statement._get_eric_xml())
        self.assertEqual(root.tag, f"{ELSTER}Elster")
        header = root.find(f"{ELSTER}TransferHeader")
        self.assertEqual(header.findtext(f"{ELSTER}Verfahren"), "ElsterAnmeldung")
        self.assertEqual(header.findtext(f"{ELSTER}DatenArt"), "UStVA")
        self.assertEqual(header.findtext(f"{ELSTER}HerstellerID"), "12345")
        self.assertIsNone(header.find(f"{ELSTER}Testmerker"))
        self.assertEqual(
            header.findtext(f"{ELSTER}DatenLieferant"),
            "Test company;Testgasse 13;;;;08151;Musterstadt;Germany;;",
        )
        block = root.find(f"{ELSTER}DatenTeil/{ELSTER}Nutzdatenblock")
        # the Bundesfinanzamtsnummer of the tax number 2893081508152
        self.assertEqual(
            block.findtext(f"{ELSTER}NutzdatenHeader/{ELSTER}Empfaenger"), "2893"
        )
        anmeldung = block.find(f"{ELSTER}Nutzdaten/{USTVA}Anmeldungssteuern")
        self.assertEqual(anmeldung.get("version"), "2025")
        # a ";" of a value doesn't shift the fields of the DatenLieferant
        self.company.name = "Test; company"
        root = etree.fromstring(self.statement._get_eric_xml())
        self.assertEqual(
            root.findtext(f"{ELSTER}TransferHeader/{ELSTER}DatenLieferant"),
            "Test, company;Testgasse 13;;;;08151;Musterstadt;Germany;;",
        )
        self.company.l10n_de_eric_test = True
        root = etree.fromstring(self.statement._get_eric_xml())
        self.assertEqual(
            root.findtext(f"{ELSTER}TransferHeader/{ELSTER}Testmerker"), "700000004"
        )

    def test_eric_xml_country(self):
        """The DatenLieferant has the German name of the country, also for a
        user of another language"""
        self.env["res.lang"]._activate_lang("de_DE")
        self.env.ref("base.de").with_context(lang="de_DE").name = "Deutschland"
        self.env.user.lang = "en_US"
        root = etree.fromstring(self.statement._get_eric_xml())
        self.assertEqual(
            root.findtext(f"{ELSTER}TransferHeader/{ELSTER}DatenLieferant"),
            "Test company;Testgasse 13;;;;08151;Musterstadt;Deutschland;;",
        )

    def test_eric_approve(self):
        """Approving opens the dialog which sends the statement"""
        with self._fake_eric():
            action = self.statement.action_approve()
        self.assertEqual(action["res_model"], "l10n.de.tax.statement.eric.send")
        self.assertEqual(action["context"]["default_declaration"], "ustva")
        self.assertEqual(self.statement.state, "draft")

    def test_eric_approve_not_configured(self):
        """Without ERiC the statement is approved for the upload"""
        with (
            patch.dict(config.options, {"l10n_de_eric_library": ""}),
            patch.dict("os.environ", {"L10N_DE_ERIC_LIBRARY": ""}),
        ):
            self.statement.action_approve()
        self.assertEqual(self.statement.state, "approved")

    def test_eric_check_failed(self):
        """An invalid statement stops the approval before the dialog"""
        with (
            self._fake_eric(fail=True),
            self.assertRaisesRegex(UserError, "Die Steuernummer ist ungültig"),
        ):
            self.statement.action_approve()
        self.assertTrue(self.calls)
        self.assertFalse(self._get_sent())
        self.assertEqual(self.statement.state, "draft")

    def test_eric_send(self):
        with self._fake_eric():
            self._send()
        _xml, _version, flags, kwargs = self.calls[-1]
        self.assertTrue(flags & ERIC_SENDE)
        self.assertEqual(kwargs["certificate"], b"pfx")
        self.assertEqual(kwargs["pin"], "1234")
        self.assertEqual(self.statement.state, "approved")
        self.assertEqual(self.statement.eric_transfer_ticket, "ab1234")
        # one message for the approval with the ticket and the protocol
        message = self.statement.message_ids.filtered("attachment_ids")
        self.assertEqual(len(message), 1)
        self.assertIn("approved and sent to ELSTER", message.body)
        self.assertIn("ab1234", message.body)
        self.assertEqual(message.attachment_ids.name, "UStVA_2025_41_Protokoll.pdf")
        with self.assertRaises(UserError):
            self.statement.action_approve()

    def test_eric_send_notes(self):
        """The approval reports the notes, not the confirmation of ELSTER"""
        with self._fake_eric(response=HINT_RESPONSE):
            self._send()
        self.assertEqual(self.statement.eric_notes, "Bitte die Kennzahl 83 prüfen.")
        message = self.statement.message_ids.filtered("attachment_ids")
        self.assertIn("Bitte die Kennzahl 83 prüfen.", message.body)
        self.assertNotIn("erfolgreich angenommen", message.body)

    def test_eric_send_without_ticket(self):
        """ERiC sent the statement, ELSTER's answer has no ticket"""
        with self._fake_eric(server_response=NO_TICKET_RESPONSE):
            self._send()
        self.assertEqual(self.statement.state, "approved")
        self.assertFalse(self.statement.eric_transfer_ticket)
        message = self.statement.message_ids.filtered("attachment_ids")
        self.assertNotIn("Transfer ticket", message.body)

    @mute_logger("odoo.addons.l10n_de_tax_statement_eric.models.l10n_de_tax_statement")
    def test_eric_send_unreadable_answer(self):
        """ELSTER has the statement once it is sent: a failure afterwards
        approves it anyway and reports the error"""
        with self._fake_eric(server_response="<broken"):
            self._send()
        self.assertEqual(self.statement.state, "approved")
        self.assertFalse(self.statement.eric_transfer_ticket)
        self.assertIn("couldn't be read", self.statement.eric_notes)
        self.assertIn("couldn't be read", self.statement.message_ids[0].body)

    @mute_logger("odoo.addons.l10n_de_tax_statement_eric.models.l10n_de_tax_statement")
    def test_eric_send_message_failed(self):
        """A failed message doesn't undo the approval of the sent statement"""
        with (
            self._fake_eric(),
            patch.object(
                type(self.statement),
                "_get_approve_message",
                side_effect=ValueError("message failed"),
            ),
        ):
            self._send()
        self.assertEqual(self.statement.state, "approved")
        self.assertEqual(self.statement.eric_transfer_ticket, "ab1234")
        self.assertTrue(self.statement.eric_protocol_id)

    def test_eric_credentials(self):
        """The certificate of the dialog wins over the stored one"""
        self.assertIsNone(self.statement._get_eric_credentials())
        self._store_credentials()
        self.assertEqual(self.statement._get_eric_credentials(), (b"stored", "4321"))
        statement = self.statement.with_context(
            l10n_de_eric_certificate=b"pfx", l10n_de_eric_pin="1234"
        )
        self.assertEqual(statement._get_eric_credentials(), (b"pfx", "1234"))

    def test_approve_access(self):
        """Only accounting administrators approve, also without the button"""
        bookkeeper = new_test_user(
            self.env,
            "eric_bookkeeper",
            groups="account.group_account_user",
            company_id=self.company.id,
        )
        self._store_credentials()
        with self._fake_eric(), self.assertRaises(AccessError):
            self.statement.with_user(bookkeeper).action_approve()
        self.assertFalse(self.calls)
        self.assertEqual(self.statement.state, "draft")

    def test_eric_send_test(self):
        self.company.l10n_de_eric_test = True
        with self._fake_eric():
            self._send()
        self.assertEqual(self.statement.state, "draft")
        self.assertFalse(self.statement.eric_transfer_ticket)
        self.assertIn("ab1234", self.statement.message_ids[0].body)

    def test_eric_send_error(self):
        with (
            self._fake_eric(fail=True),
            self.assertRaisesRegex(UserError, "Die Steuernummer ist ungültig"),
        ):
            self._send()
        self.assertEqual(self.statement.state, "draft")

    def test_eric_send_locked(self):
        """Another transaction holding the statement stops the sending"""
        execute = self.env.cr.execute

        def locked_execute(query, *args, **kwargs):
            if "FOR UPDATE NOWAIT" in str(query):
                raise errors.LockNotAvailable("could not obtain lock")
            return execute(query, *args, **kwargs)

        with (
            self._fake_eric(),
            patch.object(self.env.cr, "execute", side_effect=locked_execute),
            self.assertRaisesRegex(UserError, "Another user is changing"),
        ):
            self._send()
        self.assertFalse(self._get_sent())
        self.assertEqual(self.statement.state, "draft")

    def test_eric_send_checks(self):
        with self._fake_eric():
            with self.assertRaises(UserError):
                self._send(privacy_notice_read=False)
            with self.assertRaises(UserError):
                self._send(certificate=False)
        self.assertFalse(self.calls)

    def test_stored_certificate(self):
        """With the certificate and its PIN stored the approval sends the
        statement right away, only administrators can read them"""
        self._store_credentials()
        accountant = new_test_user(
            self.env,
            "eric_accountant",
            groups="account.group_account_manager,account.group_account_user",
            company_id=self.company.id,
        )
        for field in ("l10n_de_eric_certificate", "l10n_de_eric_pin"):
            with self.assertRaises(AccessError), mute_logger("odoo.models"):
                _ = self.company.with_user(accountant)[field]
        statement = self.statement.with_user(accountant)
        with self._fake_eric():
            # the accountant didn't confirm the privacy notice yet: the
            # dialog only asks for it
            action = statement.action_approve()
            self.assertEqual(action["res_model"], "l10n.de.tax.statement.eric.send")
            wizard = (
                self.env["l10n.de.tax.statement.eric.send"]
                .with_user(accountant)
                .with_context(**action["context"])
                .create({})
            )
            self.assertTrue(wizard.is_stored)
            self.assertFalse(wizard.privacy_notice_confirmed)
            with self.assertRaises(UserError):
                wizard.action_send()
            self.assertFalse(self._get_sent())
            wizard.privacy_notice_read = True
            wizard.action_send()
        self.assertTrue(accountant.l10n_de_eric_privacy_notice_date)
        _xml, _version, flags, kwargs = self.calls[-1]
        self.assertTrue(flags & ERIC_SENDE)
        self.assertEqual((kwargs["certificate"], kwargs["pin"]), (b"stored", "4321"))
        self.assertEqual(self.statement.state, "approved")
        self.company.l10n_de_eric_store_certificate = False
        self.assertFalse(self.company.l10n_de_eric_certificate)
        self.assertFalse(self.company.l10n_de_eric_pin)

    def test_privacy_notice_once(self):
        """The privacy notice is confirmed once per user: the next dialog
        doesn't ask for it again"""
        with self._fake_eric():
            self._send()
        date = self.env.user.l10n_de_eric_privacy_notice_date
        self.assertTrue(date)
        wizard = (
            self.env["l10n.de.tax.statement.eric.send"]
            .with_context(default_statement_id=self.statement.id)
            .create({})
        )
        self.assertTrue(wizard.privacy_notice_confirmed)
        # a second confirmation keeps the date of the first one
        self.env.user._l10n_de_eric_confirm_privacy_notice()
        self.assertEqual(self.env.user.l10n_de_eric_privacy_notice_date, date)

    def test_privacy_notice_settings(self):
        settings = self.env["res.config.settings"].create({})
        self.assertFalse(settings.l10n_de_eric_privacy_notice_date)
        settings.action_l10n_de_eric_confirm_privacy_notice()
        settings.invalidate_recordset()
        self.assertTrue(settings.l10n_de_eric_privacy_notice_date)
