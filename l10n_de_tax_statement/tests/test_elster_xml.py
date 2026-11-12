# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon

from ..models.elster_config import HERSTELLER_ID_PARAM

# The Kennzahlen of the statement in the order of the ELSTER schema, complex
# type Umsatzsteuervoranmeldung of UStVA-2025.xsd and UStVA-2026.xsd
SCHEMA_ORDER = [
    "21", "35", "36", "37", "39", "41", "42", "43", "44", "45", "46", "47",
    "48", "49", "50", "59", "60", "61", "62", "63", "64", "65", "66", "67",
    "69", "73", "74", "76", "77", "80", "81", "83", "84", "85", "86", "87",
    "89", "91", "93", "90", "94", "95", "96", "98",
]  # fmt: skip


@tagged("-at_install", "post_install")
class TestElsterXml(BaseCommon):
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
        cls.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "12345")
        cls.statement = cls.env["l10n.de.tax.statement"].create(
            {"year": 2025, "period": "41"}
        )
        cls.statement.action_update()

    def _set_amounts(self, amounts):
        for line in self.statement.line_ids:
            for field in ("base", "tax"):
                code = line[f"{field}_code"]
                if code in amounts:
                    line[field] = amounts[code]

    def _get_anmeldung(self):
        # Mein ELSTER takes the Anmeldungssteuern with its version as root
        root = etree.fromstring(self.statement._get_elster_xml())
        namespace = "http://finkonsens.de/elster/elsteranmeldung/ustva/v2025"
        self.assertEqual(root.tag, f"{{{namespace}}}Anmeldungssteuern")
        self.assertEqual(root.get("version"), "2025")
        return root, root.find(
            f"{{{namespace}}}Steuerfall/{{{namespace}}}Umsatzsteuervoranmeldung"
        )

    def _get_values(self, element):
        return [(etree.QName(child).localname, child.text) for child in element]

    def test_xml(self):
        # the bases are rounded half up to full euros
        self._set_amounts(
            {"81": 1000.50, "86": 500.49, "41": -20.50, "35": 10.0, "66": 38.0}
        )
        root, anmeldung = self._get_anmeldung()
        # the tax of Kz 81 belongs to the statement, but ELSTER computes it
        # itself from the base, so only the base is declared
        self.assertEqual(
            self._get_values(anmeldung),
            [
                ("Jahr", "2025"),
                ("Zeitraum", "41"),
                ("Steuernummer", "2893081508152"),
                ("Kz09", "12345"),
                ("Kz35", "10"),
                ("Kz36", "0.00"),
                ("Kz41", "-21"),
                ("Kz66", "38.00"),
                ("Kz81", "1001"),
                ("Kz83", f"{self.statement.tax_total:.2f}"),
                ("Kz86", "500"),
            ],
        )

    def test_xml_corrected(self):
        self.statement.is_corrected = True
        root, anmeldung = self._get_anmeldung()
        self.assertEqual(
            self._get_values(anmeldung)[3:],
            [("Kz09", "12345"), ("Kz10", "1"), ("Kz83", "0.00")],
        )

    def test_xml_widnr(self):
        # ELSTER only takes DE and the nine digits, without the suffix
        self.company.l10n_de_widnr = "DE 123456789-00001"
        root, anmeldung = self._get_anmeldung()
        self.assertEqual(self._get_values(anmeldung)[3], ("WIdNr", "DE123456789"))

    def test_xml_widnr_invalid(self):
        self.company.l10n_de_widnr = "123456789"
        with self.assertRaisesRegex(UserError, "W-IdNr"):
            self._get_anmeldung()

    def test_xml_widnr_empty(self):
        """The W-IdNr. is optional"""
        self.company.l10n_de_widnr = False
        root, anmeldung = self._get_anmeldung()
        self.assertNotIn("WIdNr", dict(self._get_values(anmeldung)))

    def test_xml_errors(self):
        self._set_amounts({"39": -1.0})
        with self.assertRaises(UserError):
            self.statement._get_elster_xml()
        self._set_amounts({"39": 1.0})
        self.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "1234")
        with self.assertRaises(UserError):
            self.statement._get_elster_xml()
        self.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "12345")
        self.company.street = False
        with self.assertRaises(UserError):
            self.statement._get_elster_xml()
        self.company.street = "Testgasse 13"
        attachment = self.statement._create_elster_xml_attachment()
        self.assertEqual(attachment.name, "UStVA_2025_41.xml")
        self.assertEqual(attachment.raw, self.statement._get_elster_xml())

    def test_xml_order(self):
        """With all Kennzahlen filled the export follows the schema order"""
        for line in self.statement.line_ids.filtered("base_code"):
            line.base = 100.0
        for line in self.statement.line_ids.filtered("tax_code"):
            line.tax = 10.0
        root, anmeldung = self._get_anmeldung()
        codes = [name[2:] for name, value in self._get_values(anmeldung)[4:]]
        self.assertEqual(codes, SCHEMA_ORDER)

    def test_xml_hersteller_id(self):
        """Without a HerstellerID there is no export"""
        self.env["ir.config_parameter"].sudo().set_param(HERSTELLER_ID_PARAM, "")
        with self.assertRaises(UserError):
            self.statement._get_elster_xml()
