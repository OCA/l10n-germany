# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import lxml.html

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged

DIN5008_LAYOUT_KEY = "l10n_din5008.external_layout_din5008"


@tagged("post_install", "-at_install")
class TestDin5008Footer(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "phone": "+49 30 123456",
                "vat": "DE123456788",
                "company_registry": "Amtsgericht Berlin HRB 12345",
                "external_report_layout_id": cls.env.ref(
                    "l10n_din5008.external_layout_din5008"
                ).id,
                "report_footer": '<p>Tel. <t t-out="object.phone">-</t></p>',
                "report_header": '<p>Call <t t-out="object.phone"/></p>',
                "company_details": '<p>Phone <t t-out="object.phone"/></p>',
                "report_layout_config": {},
            }
        )
        cls.bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "DE02120300000000202051",
                "acc_holder_name": "Acme Holding GmbH",
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.env["res.bank"].create({"name": "Musterbank"}).id,
            }
        )
        cls.env["ir.ui.view"].create(
            {
                "name": "l10n_din5008_footer.test_lines",
                "type": "qweb",
                "inherit_id": cls.env.ref("l10n_de_report_footer.footer_lines").id,
                "mode": "extension",
                "arch": """
                    <xpath expr="//t[@name='l10n_de_report_footer_lines']"
                           position="inside">
                        <li class="test_footer_line">Registergericht Berlin</li>
                    </xpath>
                """,
            }
        )

    def _preview(self, config=None):
        """Preview of the wizard with the given (unsaved) settings merged in."""
        with Form(self.env["base.document.layout"]) as wizard:
            self.assertEqual(
                wizard.report_layout_id,
                self.env.ref("l10n_din5008.report_layout_din5008"),
            )
            if config:
                wizard.report_layout_config = {
                    **(wizard.report_layout_config or {}),
                    **config,
                }
            preview = wizard.preview
            # discard: the preview is enough, the company is not written
            wizard.report_layout_config = dict(self.company.report_layout_config or {})
        return preview

    def _footer(self, preview):
        tree = lxml.html.fromstring(preview)
        footers = tree.xpath(
            "//div[contains(@class, 'din_page') and contains(@class, 'footer')]"
        )
        self.assertEqual(len(footers), 1)
        return footers[0]

    def test_preview_footer(self):
        preview = self._preview()
        self.assertIn("din_page footer", preview)
        self.assertIn("Tel. +49 30 123456", preview)
        self.assertIn("Call +49 30 123456", preview)
        self.assertIn("Phone +49 30 123456", preview)
        self.assertNotIn("t-out=", preview)
        # the footer lines are printed before the VAT number
        self.assertLess(
            preview.index("Registergericht Berlin"), preview.index("DE123456788")
        )
        # the texts carry the classes of the preview highlight
        tree = lxml.html.fromstring(preview)
        for css_class, text in (
            ("o_report_footer_text", "Tel. +49 30 123456"),
            ("o_report_company_details", "Phone +49 30 123456"),
            ("o_report_tagline", "Call +49 30 123456"),
        ):
            nodes = tree.xpath(f"//*[contains(@class, '{css_class}')]")
            self.assertEqual(len(nodes), 1, css_class)
            self.assertIn(text, nodes[0].text_content(), css_class)
        footer = self._footer(preview)
        self.assertIn("Amtsgericht Berlin HRB 12345", footer.text_content())
        self.assertNotIn("Account Holder", footer.text_content())
        self.assertFalse(footer.xpath("./style"))
        # the preview is scoped to the (new) wizard record
        self.assertTrue(
            any(
                cls.startswith("o_report_footer_")
                for cls in footer.get("class").split()
            )
        )

    def test_bank_account_holder(self):
        footer = self._footer(self._preview({"footer.bank_acc_holder": True}))
        text = footer.text_content()
        holders = [
            " ".join(li.text_content().split())
            for li in footer.xpath(".//li[@name='bank_acc_holder']")
        ]
        self.assertEqual(holders.count("Account Holder: Acme Holding GmbH"), 1)
        self.assertLess(text.index("Musterbank"), text.index("Acme Holding GmbH"))

    def test_specs(self):
        Company = self.env["res.company"]
        specs = Company._get_report_layout_config_fields_by_key()
        for key, default in (
            ("footer.bank_acc_holder", False),
            ("footer.table_width_pattern", ""),
        ):
            self.assertEqual(specs[key]["section"], "footer")
            self.assertEqual(specs[key]["default"], default)
            self.assertEqual(specs[key]["layouts"], [DIN5008_LAYOUT_KEY])
            self.assertEqual(specs[key]["highlight"], "footer")
        self.assertEqual(
            specs["footer.table_width_pattern"]["validate"],
            "_validate_din5008_footer_table_widths",
        )
        # offered for the DIN 5008 layout of Odoo only
        offered = Company.get_report_layout_config_fields(DIN5008_LAYOUT_KEY)
        offered = [s["key"] for s in offered]
        self.assertIn("footer.bank_acc_holder", offered)
        self.assertIn("footer.table_width_pattern", offered)
        offered = [
            s["key"]
            for s in Company.get_report_layout_config_fields(
                "web.external_layout_standard"
            )
        ]
        self.assertNotIn("footer.bank_acc_holder", offered)
        self.assertNotIn("footer.table_width_pattern", offered)
        with Form(self.env["base.document.layout"]) as wizard:
            keys = [spec["key"] for spec in wizard.report_layout_config_fields]
            self.assertIn("footer.table_width_pattern", keys)

    def test_table_widths(self):
        company = self.company
        self.assertIsNone(company._get_din5008_footer_table_widths())
        for value in ("25,25", "a,b,c,d", "25,25,25,30", "0,50,25,25", "-5,55,25,25"):
            with self.assertRaises(ValidationError, msg=value):
                company._set_report_layout_config_value(
                    "footer.table_width_pattern", value=value
                )
            self.assertIsNone(company._parse_din5008_footer_table_widths(value))
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value(
                "footer.table_width_pattern", value=25
            )
        for value in ("", "  "):
            company._set_report_layout_config_value(
                "footer.table_width_pattern", value=value
            )
            self.assertIsNone(company._get_din5008_footer_table_widths())
        company._set_report_layout_config_value(
            "footer.table_width_pattern", value=" 25, 35.5,19.5 ,20 "
        )
        self.assertEqual(
            company._get_din5008_footer_table_widths(), [25, 35.5, 19.5, 20]
        )

    def test_footer_css(self):
        company = self.company
        self.assertEqual(company._render_din5008_footer_css(), "")
        company._set_report_layout_config_value(
            "footer.table_width_pattern", value="25,35,20,20"
        )
        table = (
            f".{company._get_report_footer_scope_class()}.footer .company_details table"
        )
        css = company._render_din5008_footer_css()
        self.assertEqual(
            css.splitlines(),
            [
                f"{table} td:nth-child(1) {{ width: 25%; }}",
                f"{table} td:nth-child(2) {{ width: 35%; }}",
                f"{table} td:nth-child(3) {{ width: 20%; }}",
                f"{table} td:nth-child(4) {{ width: 20%; }}",
            ],
        )
        # printed inside the footer of the preview, scoped to the wizard
        footer = self._footer(self._preview())
        styles = footer.xpath("./style")
        self.assertEqual(len(styles), 1)
        self.assertIn("td:nth-child(4) { width: 20%; }", styles[0].text)
        self.assertIn(".footer .company_details table td:nth-child(1)", styles[0].text)
