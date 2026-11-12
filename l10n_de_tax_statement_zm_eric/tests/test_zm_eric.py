# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from unittest.mock import patch

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import config, mute_logger

from odoo.addons.l10n_de_tax_statement.models.elster_config import (
    HERSTELLER_ID_PARAM,
)
from odoo.addons.l10n_de_tax_statement_eric.tests.common import EricFakeCase
from odoo.addons.l10n_de_tax_statement_eric.tools.eric import ERIC_SENDE

ELSTER = "{http://www.elster.de/elsterxml/schema/v11}"


def zm_sending_fails(datenart_version, sending):
    return sending and datenart_version == "ZMDO"


def zm_check_fails(datenart_version, sending):
    return not sending and datenart_version == "ZMDO"


@tagged("-at_install", "post_install")
class TestZmEric(EricFakeCase):
    fake_tickets = {"ZMDO": "zm1234"}

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
                "phone": "+49 (0815) 999-99",
                "vat": "DE123456788",
            }
        )
        cls.company.l10n_de_stnr = "93815/08152"
        cls.env.company = cls.company
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        cls.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "12345")
        cls.env["account.chart.template"].try_loading("de_skr03", cls.company)
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "sale")], limit=1
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.env.ref("base.nl").id,
                "vat": "NL000099998B57",
            }
        )
        invoice_form = Form(
            cls.env["account.move"].with_context(
                default_move_type="out_invoice", default_journal_id=cls.journal.id
            )
        )
        invoice_form.partner_id = cls.partner
        invoice_form.invoice_date = date(2025, 3, 15)
        for price_unit, xmlid in (
            (100.4, "tax_eu_sale_skr03"),
            (50.0, "tax_free_eu_skr03"),
        ):
            with invoice_form.invoice_line_ids.new() as line:
                line.name = "Test line"
                line.price_unit = price_unit
                line.tax_ids.clear()
                line.tax_ids.add(cls.env.ref(f"account.{cls.company.id}_{xmlid}"))
        invoice_form.save().action_post()
        cls.statement = cls.env["l10n.de.tax.statement"].create(
            {"year": 2025, "period": "03"}
        )
        cls.statement.action_update()

    def test_zm_eric_xml(self):
        xml = self.statement._get_zm_eric_xml()
        # ERiC needs the namespace declared on the root of the Nutzdaten
        self.assertIn(
            b'<zm xmlns="http://www.elster.de/elsterxml/schema/v11" version="000005">',
            xml,
        )
        root = etree.fromstring(xml)
        header = root.find(f"{ELSTER}TransferHeader")
        self.assertEqual(header.findtext(f"{ELSTER}Verfahren"), "ElsterExtern")
        self.assertEqual(header.findtext(f"{ELSTER}DatenArt"), "ZMDO")
        block = root.find(f"{ELSTER}DatenTeil/{ELSTER}Nutzdatenblock")
        empfaenger = block.find(f"{ELSTER}NutzdatenHeader/{ELSTER}Empfaenger")
        self.assertEqual((empfaenger.get("id"), empfaenger.text), ("L", "BF"))
        unternehmer = block.find(f"{ELSTER}Nutzdaten/{ELSTER}zm/{ELSTER}unternehmer")
        self.assertEqual(unternehmer.findtext(f"{ELSTER}knri"), "DE123456788")
        anschrift = unternehmer.find(f"{ELSTER}anschrift")
        self.assertEqual(anschrift.findtext(f"{ELSTER}staat"), "DE")
        self.assertEqual(anschrift.findtext(f"{ELSTER}telefon"), "+49 (0815) 999-99")
        zm_zeilen = unternehmer.find(f"{ELSTER}zm-zeilen")
        self.assertEqual(zm_zeilen.get("meldeart"), "10")
        self.assertEqual(zm_zeilen.findtext(f"{ELSTER}mzr/{ELSTER}quart"), "23")
        self.assertEqual(zm_zeilen.findtext(f"{ELSTER}mzr/{ELSTER}jahr"), "2025")
        self.assertEqual(
            [
                (
                    zeile.get("umsatzart"),
                    zeile.findtext(f"{ELSTER}knre"),
                    zeile.findtext(f"{ELSTER}betrag"),
                )
                for zeile in zm_zeilen.iterfind(f"{ELSTER}zeile")
            ],
            [("L", "NL000099998B57", "100"), ("S", "NL000099998B57", "50")],
        )

    def test_zm_quart(self):
        statement = self.env["l10n.de.tax.statement"].new({"year": 2025})
        for period, quart in (("01", 21), ("12", 32), ("41", 1), ("44", 4)):
            statement.period = period
            self.assertEqual(statement._get_zm_quart(), quart)

    def test_zm_eric_no_vat(self):
        self.company.vat = False
        with self.assertRaises(UserError):
            self.statement._get_zm_eric_xml()

    def test_zm_eric_send(self):
        """Approving sends the ZM along with the statement"""
        with self._fake_eric():
            self._send(self.statement.action_approve())
        # ERiC validated the ZM before anything was sent
        first_sent = next(
            index for index, call in enumerate(self.calls) if call[2] & ERIC_SENDE
        )
        self.assertIn("ZMDO", [call[1] for call in self.calls[:first_sent]])
        self.assertEqual(self._get_sent(), ["UStVA_2025", "ZMDO"])
        self.assertEqual(self.statement.state, "approved")
        self.assertTrue(self.statement.zm_is_sent)
        self.assertEqual(self.statement.zm_eric_transfer_ticket, "zm1234")
        # one message for the approval with the statement and the ZM
        message = self.statement.message_ids[0]
        self.assertIn("The ZM is sent to the BZSt.", message.body)
        self.assertEqual(
            sorted(message.attachment_ids.mapped("name")),
            ["UStVA_2025_03_Protokoll.pdf", "ZM_2025_03_Protokoll.pdf"],
        )
        with self.assertRaises(UserError):
            self.statement._eric_send_zm()

    def test_zm_eric_check_failed(self):
        """An invalid ZM stops the approval before anything is sent"""
        with self._fake_eric(fail=zm_check_fails), self.assertRaises(UserError):
            self.statement.action_approve()
        self.assertIn("ZMDO", [call[1] for call in self.calls])
        self.assertFalse(self._get_sent())
        self.assertEqual(self.statement.state, "draft")

    def test_zm_eric_send_failed(self):
        """A failed ZM leaves the statement approved, the ZM can be sent again"""
        with self._fake_eric(fail=zm_sending_fails):
            self._send(self.statement.action_approve())
        self.assertEqual(self.statement.state, "approved")
        self.assertFalse(self.statement.zm_is_sent)
        self.assertTrue(self.statement.zm_eric_error)
        self.assertIn("The ZM isn't sent", self.statement.message_ids[0].body)
        # a test transmission doesn't send the ZM of an approved statement
        self.company.l10n_de_eric_test = True
        with self._fake_eric(), self.assertRaises(UserError):
            self.statement.action_zm_eric_send()
        self.assertFalse(self.calls)
        self.company.l10n_de_eric_test = False
        with self._fake_eric():
            self._send(self.statement.action_zm_eric_send())
        self.assertEqual(self._get_sent(), ["ZMDO"])
        self.assertTrue(self.statement.zm_is_sent)
        self.assertFalse(self.statement.zm_eric_error)
        # sent again on its own, the ZM has a message of its own
        message = self.statement.message_ids[0]
        self.assertIn("zm1234", message.body)
        self.assertEqual(message.attachment_ids.name, "ZM_2025_03_Protokoll.pdf")

    @mute_logger(
        "odoo.addons.l10n_de_tax_statement_zm_eric.models.l10n_de_tax_statement"
    )
    def test_zm_eric_send_unexpected_error(self):
        """Any failure of the ZM leaves the sent statement approved"""
        with (
            self._fake_eric(),
            patch.object(
                type(self.statement),
                "_eric_send_zm",
                side_effect=ValueError("unexpected"),
            ),
        ):
            self._send(self.statement.action_approve())
        self.assertEqual(self.statement.state, "approved")
        self.assertEqual(self.statement.zm_eric_error, "unexpected")
        self.assertIn("The ZM isn't sent", self.statement.message_ids[0].body)

    def test_zm_eric_send_not_configured(self):
        """Without ERiC the ZM can't be sent again: it is uploaded"""
        with (
            patch.dict(config.options, {"l10n_de_eric_library": ""}),
            patch.dict("os.environ", {"L10N_DE_ERIC_LIBRARY": ""}),
        ):
            self.statement.action_approve()
            self.assertEqual(self.statement.state, "approved")
            self.statement.invalidate_recordset(["is_eric_used"])
            self.assertFalse(self.statement.is_eric_used)
            with self.assertRaisesRegex(UserError, "ERiC isn't configured"):
                self.statement.action_zm_eric_send()

    def test_zm_eric_send_stored(self):
        """With the stored certificate the ZM is sent again right away"""
        with self._fake_eric(fail=zm_sending_fails):
            self._send(self.statement.action_approve())
        self._store_credentials()
        with self._fake_eric():
            self.assertIs(self.statement.action_zm_eric_send(), True)
        self.assertEqual(self._get_sent(), ["ZMDO"])
        self.assertEqual(self.calls[-1][3]["certificate"], b"stored")
        self.assertTrue(self.statement.zm_is_sent)

    def test_zm_eric_send_test_failed(self):
        """A failed test ZM is reported in a message of its own"""
        self.company.l10n_de_eric_test = True
        with self._fake_eric(fail=zm_sending_fails):
            self._send(self.statement.action_approve())
        self.assertEqual(self.statement.state, "draft")
        self.assertFalse(self.statement.zm_eric_error)
        self.assertIn("The ZM failed", self.statement.message_ids[0].body)

    def test_zm_eric_send_test(self):
        self.company.l10n_de_eric_test = True
        with self._fake_eric():
            self._send(self.statement.action_approve())
        self.assertEqual(self.statement.state, "draft")
        self.assertFalse(self.statement.zm_is_sent)
        self.assertIn("zm1234", self.statement.message_ids[0].body)
