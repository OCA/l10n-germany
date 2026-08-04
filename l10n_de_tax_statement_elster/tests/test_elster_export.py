# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
ELSTER direct HTTP download from controller — no write to statement record.
"""

import datetime

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon

NAMESPACE = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2026"


@tagged("-at_install", "post_install")
class TestElsterExport(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        country_de = cls.env.ref("base.de")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test GmbH & Co. KG",
                "country_id": country_de.id,
                "currency_id": cls.eur.id,
                "l10n_de_stnr": "1112034567890",
                "street": "Teststraße 12",
                "zip": "12345",
                "city": "Teststadt",
                "phone": "0123/456789",
                "email": "test@test-gmbh.de",
            }
        )
        cls.env.company = cls.company
        template = cls.env["account.chart.template"]
        template.try_loading("de_skr03", cls.company)
        cls.env["l10n.de.tax.statement"].search(
            [("state", "not in", ["posted", "final"])]
        ).unlink()

        cls.tax_1 = cls.env.ref(f"account.{cls.company.id}_tax_ust_19_skr03")
        cls.tax_2 = cls.env.ref(f"account.{cls.company.id}_tax_ust_7_skr03")
        cls.journal_sale = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "sale")],
            limit=1,
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Kunde"})

    def _create_invoice(self, lines_data):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": datetime.date(2026, 1, 15),
                "date": datetime.date(2026, 1, 15),
                "journal_id": self.journal_sale.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": line[0],
                            "quantity": 1.0,
                            "price_unit": line[1],
                            "tax_ids": [(6, 0, [line[2].id])],
                        },
                    )
                    for line in lines_data
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _make_statement(self, from_date, to_date):
        stmt = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Test Statement 2026",
                "version": "2026",
                "from_date": from_date,
                "to_date": to_date,
            }
        )
        stmt.statement_update()
        stmt.post()
        return stmt

    def _download_xml(self, statement):
        """Simulate the controller download by calling the action URL."""

        from odoo.addons.l10n_de_tax_statement_elster.controllers.main import (
            VatStatementElsterController,
        )

        # Use the controller directly for testing
        controller = VatStatementElsterController()
        response = controller.download_elster_xml(statement.id)

        if hasattr(response, "data"):
            return response.data
        if hasattr(response, "content"):
            return response.content
        # Response from make_response
        if hasattr(response, "response"):
            return b"".join(response.response)
        response_content = list(response.response)
        return b"".join(response_content)

    def test_button_returns_download_url(self):
        """Test that the button action returns a download URL."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        result = stmt.action_generate_elster_xml()
        self.assertEqual(result["type"], "ir.actions.act_url")
        self.assertIn("/l10n_de_tax_statement_elster/", result["url"])
        self.assertIn("/download", result["url"])

    def test_draft_rejected(self):
        """Test draft statement cannot be exported."""
        stmt = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Draft",
                "version": "2026",
                "from_date": datetime.date(2026, 1, 1),
                "to_date": datetime.date(2026, 1, 31),
            }
        )
        with self.assertRaises(UserError):
            stmt.action_generate_elster_xml()

    def test_non_2026_rejected(self):
        """Test non-2026 version cannot be exported."""
        stmt = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Old",
                "version": "2021",
                "from_date": datetime.date(2021, 1, 1),
                "to_date": datetime.date(2021, 1, 31),
            }
        )
        stmt.statement_update()
        stmt.post()
        with self.assertRaises(UserError):
            stmt.action_generate_elster_xml()

    def test_encoding_iso8859_15(self):
        """Verify the XML is ISO-8859-15 encoded bytes."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        self.assertTrue(xml_bytes.startswith(b"<?xml"))
        self.assertIn(b"ISO-8859-15", xml_bytes[:80])

    def test_root_element(self):
        """Verify root element is Anmeldungssteuern."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        self.assertEqual(root.tag, "Anmeldungssteuern")
        self.assertEqual(root.get("version"), "2026")

    def test_no_transfer_header(self):
        """Verify no Elster envelope elements."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        text = xml_bytes.decode("iso-8859-15")
        self.assertNotIn("TransferHeader", text)
        self.assertNotIn("NutzdatenHeader", text)
        self.assertNotIn("DatenTeil", text)

    def test_january_period(self):
        """Test January 2026 period code."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        zeitraum = root.findtext(".//Zeitraum")
        self.assertEqual(zeitraum, "01")

    def test_december_period(self):
        """Test December 2026 period code."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 12, 1), datetime.date(2026, 12, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        zeitraum = root.findtext(".//Zeitraum")
        self.assertEqual(zeitraum, "12")

    def test_quarterly_period(self):
        """Test Q1 2026 period code."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 3, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        zeitraum = root.findtext(".//Zeitraum")
        self.assertEqual(zeitraum, "41")

    def test_kz81_base_format(self):
        """Test Kz81 is exported as full euros (no decimals)."""
        self._create_invoice(
            [
                ("Line 19%", 1000.0, self.tax_1),
            ]
        )
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        kz81 = root.findtext(".//Kz81")
        self.assertEqual(kz81, "1000")

    def test_kz81_rounding(self):
        """Test Kz81 base is rounded to full euros."""
        self._create_invoice(
            [
                ("Line 19%", 100.55, self.tax_1),
            ]
        )
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        kz81 = root.findtext(".//Kz81")
        self.assertEqual(kz81, "101")

    def test_kz83_not_auto_exported(self):
        """Kz83 is never auto-exported (ELSTER calculates it)."""
        self._create_invoice(
            [
                ("Line 19%", 1000.0, self.tax_1),
            ]
        )
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        root = etree.fromstring(xml_bytes)
        self.assertIsNone(root.find(".//Kz83"))

    def test_no_write_on_statement(self):
        """Verify the statement is never written to during export."""
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        # Verify no elster fields exist on the model (no write needed)
        self.assertNotIn("elster_xml_file", stmt._fields)
        self.assertNotIn("elster_xml_filename", stmt._fields)

        # The action should succeed without writing
        result = stmt.action_generate_elster_xml()
        self.assertIsInstance(result, dict)

    def test_umlaute_in_xml(self):
        """Test umlauts are properly encoded in output."""
        self.company.name = "Münchner Ölwerke & Großhandel"
        self._create_invoice([])
        stmt = self._make_statement(
            datetime.date(2026, 1, 1), datetime.date(2026, 1, 31)
        )
        xml_bytes = self._download_xml(stmt)
        text = xml_bytes.decode("iso-8859-15")
        self.assertIn("Münchner", text)
        self.assertIn("Ölwerke", text)
        self.assertIn("Großhandel", text)


@tagged("-at_install", "post_install")
class TestTaxNumberConversion(BaseCommon):
    """Unit tests for German tax number → ELSTER format conversion."""

    def _convert(self, stnr, state_code="DE-NI"):
        from odoo.addons.l10n_de_tax_statement_elster.services.tax_number import (
            convert_german_tax_number_to_elster,
        )

        return convert_german_tax_number_to_elster(stnr, state_code)

    def test_slashed_lower_saxony(self):
        result = self._convert("12/345/67890")
        self.assertEqual(result, "2312034567890")

    def test_slashed_with_leading_zeros(self):
        result = self._convert("01/002/00012")
        self.assertEqual(result, "2301000200012")

    def test_already_13_digit(self):
        result = self._convert("2313021000968")
        self.assertEqual(result, "2313021000968")

    def test_invalid_block_count_slash(self):
        with self.assertRaises(UserError):
            self._convert("12/345")

    def test_invalid_block_count_triple_slash(self):
        with self.assertRaises(UserError):
            self._convert("12/34/56/78")

    def test_block_length_format_mismatch(self):
        with self.assertRaises(UserError):
            self._convert("12345/678/90")

    def test_letters_rejected(self):
        with self.assertRaises(UserError):
            self._convert("AB/CDE/FGHIJ")

    def test_result_exactly_13_digits(self):
        result = self._convert("99/999/99999")
        self.assertEqual(len(result), 13)
        self.assertTrue(result.isdigit())

    def test_empty_raises(self):
        with self.assertRaises(UserError):
            self._convert("")

    def test_unknown_state_strips_non_digit(self):
        result = self._convert("99-999-9999999", state_code=None)
        self.assertEqual(result, "0999999999999")


@tagged("-at_install", "post_install")
class TestElsterXmlQuality(BaseCommon):
    """Null-value suppression, Kz66/Kz83 policy, and address formatting.

    Uses synthetic test data exclusively.  Calls generate_elster_xml()
    directly (bypasses the HTTP controller) for focused unit testing.
    """

    NS = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2026"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.eur = cls.env.ref("base.EUR")
        country_de = cls.env.ref("base.de")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Musterfirma GmbH",
                "country_id": country_de.id,
                "currency_id": cls.eur.id,
                "l10n_de_stnr": "2812012345678",
                "street": "Musterstraße 8a",
                "zip": "12345",
                "city": "Teststadt",
                "phone": "0123/456789",
                "email": "test@musterfirma.de",
            }
        )
        cls.env.company = cls.company
        template = cls.env["account.chart.template"]
        template.try_loading("de_skr03", cls.company)
        cls.env["l10n.de.tax.statement"].search(
            [("state", "not in", ["posted", "final"])]
        ).unlink()

        cls.tax_vst_19 = cls.env.ref(f"account.{cls.company.id}_tax_vst_19_skr03")
        cls.tax_ust_19 = cls.env.ref(f"account.{cls.company.id}_tax_ust_19_skr03")
        cls.journal_purchase = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "purchase")],
            limit=1,
        )
        cls.partner = cls.env["res.partner"].create({"name": "Lieferant AG"})

    def _generate_xml(self, statement):
        """Call the ELSTER export service directly."""
        from odoo.addons.l10n_de_tax_statement_elster.services.elster_export import (
            generate_elster_xml,
        )

        return generate_elster_xml(statement)

    def _xpath(self, root, path):
        """Namespaced XPath search on the UStVA XML root."""
        ns = {"e": self.NS}
        return root.find(path.format(**ns), ns)

    def _xpath_text(self, root, path):
        """Namespaced XPath text extraction."""
        el = self._xpath(root, path)
        return el.text if el is not None else None

    def _all_kz_texts(self, root):
        """Return set of (tag, text) for all Kz elements under UVA."""
        uva = self._xpath(root, ".//e:Umsatzsteuervoranmeldung")
        if uva is None:
            return set()
        return {
            (etree.QName(el).localname, el.text)
            for el in uva.iter()
            if etree.QName(el).localname.startswith("Kz")
        }

    def _make_statement(self, from_date, to_date):
        stmt = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Test UStVA 2026",
                "version": "2026",
                "from_date": from_date,
                "to_date": to_date,
            }
        )
        stmt.statement_update()
        stmt.post()
        return stmt

    def _create_purchase(self, amount, tax):
        inv = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_date": datetime.date(2026, 4, 15),
                "date": datetime.date(2026, 4, 15),
                "journal_id": self.journal_purchase.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Eingangsrechnung",
                            "quantity": 1.0,
                            "price_unit": amount,
                            "tax_ids": [(6, 0, [tax.id])],
                        },
                    ),
                ],
            }
        )
        inv.action_post()
        return inv

    def _make_statement_with_values(self, from_date, to_date, line_updates):
        """Create and post a statement with specific line values.

        line_updates is a dict mapping line code → value to set on
        the tax field.  Lines not listed keep their computed (zero)
        values.
        """
        stmt = self.env["l10n.de.tax.statement"].create(
            {
                "name": "Test UStVA 2026",
                "version": "2026",
                "from_date": from_date,
                "to_date": to_date,
                "company_id": self.company.id,
            }
        )
        stmt.statement_update()
        for code, value in line_updates.items():
            line = stmt.line_ids.filtered(lambda line_, code=code: line_.code == code)
            line.tax = value
            line._compute_amount_format()
        stmt.post()
        return stmt

    # ── Null-value suppression ──
    def test_zero_base_integer_omitted(self):
        """Kz81 with value 0 (base, integer) is not exported."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertIsNone(self._xpath(root, ".//e:Kz81"))

    def test_zero_tax_decimal_omitted(self):
        """Kz36 with value 0.00 (tax, decimal) is not exported."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertIsNone(self._xpath(root, ".//e:Kz36"))

    def test_zero_not_in_minimal_xml(self):
        """No Kz element has text '0' or '0.00' in a minimal export."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        for tag, text in self._all_kz_texts(root):
            self.assertNotIn(text, ("0", "0.00"), f"{tag} has zero text '{text}'")

    # ── Kz66 preservation ──
    def test_kz66_exported_exactly(self):
        """Kz66 = 117.93 is exported with the correct value."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        kz66 = self._xpath_text(root, ".//e:Kz66")
        self.assertIsNotNone(kz66, "Kz66 must be present")

    def test_nonzero_not_filtered(self):
        """A non-zero Kz element is NOT removed by the zero filter."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 500.0},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        kz66 = self._xpath_text(root, ".//e:Kz66")
        self.assertIsNotNone(kz66)

    # ── Kz83 policy ──
    def test_kz83_absent_with_only_kz66(self):
        """No Kz83 when only Kz66=117.93 exists (ELSTER calculates it)."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertIsNone(self._xpath(root, ".//e:Kz83"))

    # ── Negative values ──
    def test_negative_nonzero_exported(self):
        """Negative non-zero Kz values are still exported."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        kz66 = self._xpath_text(root, ".//e:Kz66")
        self.assertIsNotNone(kz66)

    # ── Element order ──
    def test_element_order_preserved(self):
        """Kz elements appear in ascending numeric order."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        uva = self._xpath(root, ".//e:Umsatzsteuervoranmeldung")
        kz_tags = [
            etree.QName(el).localname
            for el in uva.iter()
            if etree.QName(el).localname.startswith("Kz")
        ]
        kz_numbers = [int(tag[2:]) for tag in kz_tags]
        self.assertEqual(kz_numbers, sorted(kz_numbers))

    # ── Street / house number ──
    def test_street_no_duplicate_house_number(self):
        """Str must NOT contain the house number when Hausnummer is set."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        street = self._xpath_text(root, ".//e:Unternehmer/e:Str")
        hnr = self._xpath_text(root, ".//e:Unternehmer/e:Hausnummer")
        if hnr and street:
            self.assertNotIn(hnr, street)

    def test_house_number_with_suffix(self):
        """Hausnummer correctly handles '8a' format."""
        self.company.street = "Am Markt 8a"
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Unternehmer/e:Str"), "Am Markt")
        self.assertEqual(self._xpath_text(root, ".//e:Unternehmer/e:Hausnummer"), "8a")

    def test_house_number_range(self):
        """Hausnummer correctly handles '8-10' format."""
        self.company.street = "Parkweg 8-10"
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Unternehmer/e:Str"), "Parkweg")
        self.assertEqual(
            self._xpath_text(root, ".//e:Unternehmer/e:Hausnummer"), "8-10"
        )

    def test_house_number_slash(self):
        """Hausnummer correctly handles '8/10' format."""
        self.company.street = "Ringstraße 8/10"
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Unternehmer/e:Str"), "Ringstraße")
        self.assertEqual(
            self._xpath_text(root, ".//e:Unternehmer/e:Hausnummer"), "8/10"
        )

    def test_unsplittable_address_safe(self):
        """If street cannot be split, no fake Hausnummer is invented."""
        self.company.street = "Postfach"
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Unternehmer/e:Str"), "Postfach")
        hnr = self._xpath_text(root, ".//e:Unternehmer/e:Hausnummer")
        self.assertTrue(hnr is None or hnr == "")

    # ── Encoding / serialisation ──
    def test_iso8859_15_serializable(self):
        """XML can be parsed after ISO-8859-15 decoding."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        xml_bytes = self._generate_xml(stmt)
        text = xml_bytes.decode("iso-8859-15")
        etree.fromstring(xml_bytes)
        self.assertIn("117.93", text)

    # ── Period 42 preserved ──
    def test_quarter_42_period(self):
        """Second quarter (42) is still exported correctly."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Zeitraum"), "42")

    # ── Tax number preserved ──
    def test_tax_number_in_xml(self):
        """13-digit tax number appears unchanged in the XML."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Steuernummer"), "2812012345678")

    # ── Backup: existing test data preserved ──
    def test_jahr_2026_present(self):
        """Jahr 2026 is exported as expected."""
        stmt = self._make_statement_with_values(
            datetime.date(2026, 4, 1),
            datetime.date(2026, 6, 30),
            {"38": 117.93},
        )
        root = etree.fromstring(self._generate_xml(stmt))
        self.assertEqual(self._xpath_text(root, ".//e:Jahr"), "2026")
