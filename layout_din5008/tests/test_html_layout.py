# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from .common import LayoutDin5008Common

HEADER = "//div[contains(concat(' ', normalize-space(@class), ' '), ' header ')]"
ARTICLE = "//div[contains(concat(' ', normalize-space(@class), ' '), ' article ')]"
FOOTER = "//div[contains(concat(' ', normalize-space(@class), ' '), ' footer ')]"
ADDRESS_ROW = "//div[contains(concat(' ', normalize-space(@class), ' '), ' address ')]"


@tagged("post_install", "-at_install")
class TestHtmlLayout(LayoutDin5008Common, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_din5008()

    def _one(self, tree, xpath):
        nodes = tree.xpath(xpath)
        self.assertEqual(len(nodes), 1, f"expected one node for {xpath}")
        return nodes[0]

    def test_structure_below(self):
        self._write_config({"din5008.informations_position": "below"})
        tree = self._render_tree()
        header = self._one(tree, HEADER)
        article = self._one(tree, ARTICLE)
        footer = self._one(tree, FOOTER)
        company_class = f"o_company_{self.company.id}_layout"
        for node in (header, article, footer):
            self.assertIn("o_layout_din5008", node.get("class"))
            self.assertIn(company_class, node.get("class"))
        self.assertIn("o_report_layout_standard", article.get("class"))
        self.assertEqual(header.get("style"), "height: 27mm;")
        self.assertEqual(header.get("data-din5008-form"), "A")
        self.assertEqual(header.get("data-din5008-logo"), "left")
        self.assertEqual(article.get("data-din5008-informations"), "below")

        # the address is printed as sender line only; VAT and footer lines
        # are moved into the footer
        self.assertFalse(tree.xpath("//div[@name='company_address']"))
        legal = self._one(footer, ".//ul[@name='din5008_footer_legal']")
        self.assertIn("DE123456788", legal.text_content())
        self.assertNotIn("DE123456788", header.text_content())
        # footer text as a full width block after the company / page number row
        footer_text = self._one(
            footer, ".//div[contains(@class, 'din5008_footer_text')]"
        )
        self.assertIn("Tel. +49 30 123456", footer_text.text_content())
        self.assertIn("o_report_footer_text", footer_text.get("class"))
        content = self._one(footer, ".//div[contains(@class, 'o_footer_content')]")
        self.assertIs(content.getnext(), footer_text)
        self.assertIsNone(footer.get("style"))
        self.assertFalse(
            content.xpath(".//div[contains(@class, 'din5008_footer_text')]")
        )

        # fold marks: two fold marks and one hole mark in the header
        marks = header.xpath(".//div[contains(@class, 'din5008_fold_mark')]")
        self.assertEqual([m.get("style") for m in marks], ["top: 87mm;", "top: 192mm;"])
        hole = self._one(header, ".//div[contains(@class, 'din5008_hole_mark')]")
        self.assertEqual(hole.get("style"), "top: 148.5mm;")

        # sender line above the address window
        sender = self._one(article, ".//div[@class='din5008_sender_line']")
        self.assertEqual(
            sender.text_content(), "Acme GmbH | Musterstraße 1 | 12345 Berlin"
        )
        self.assertEqual(sender.get("style"), "top: 0mm;")

        # standard address row with the information block after the address
        row = self._one(article, ADDRESS_ROW)
        children = [child.get("name") for child in row if child.get("name")]
        self.assertEqual(children, ["address", "information_block"])
        self.assertIn("Max Mustermann", row.text_content())
        self.assertIn("Lager Nord", row.text_content())

        # document information stays inside the page
        informations = self._one(article, ".//div[@id='informations']")
        self.assertTrue(informations.xpath("ancestor::div[@class='page']"))
        self.assertFalse(article.xpath(".//div[@name='din5008_informations']"))
        title = self._one(article, "./h2")
        self.assertEqual(title.text_content().strip(), "Rechnung RE-2026-001")
        # company specific css is scoped to the article
        style = self._one(article, "./style")
        self.assertIn(self.company._layout_din5008_scope_class(), style.text)
        self.assertIn(self.company._layout_din5008_scope_class(), article.get("class"))
        self.assertIn("min-height: 45mm", style.text)

    def test_structure_beside(self):
        # "beside" is the default
        tree = self._render_tree()
        article = self._one(tree, ARTICLE)
        self.assertEqual(article.get("data-din5008-informations"), "beside")
        row = self._one(article, ADDRESS_ROW)
        children = [child.get("name") for child in row if child.get("name")]
        self.assertEqual(
            children, ["address", "information_block", "din5008_informations"]
        )
        informations = self._one(article, ".//div[@id='informations']")
        self.assertTrue(
            informations.xpath("ancestor::div[@name='din5008_informations']")
        )
        self.assertFalse(informations.xpath("ancestor::div[@class='page']"))
        self.assertIn("Rechnungsdatum", row.text_content())
        page = self._one(article, ".//div[@class='page']")
        self.assertIn("Position 1", page.text_content())
        self.assertNotIn("Rechnungsdatum", page.text_content())
        # the title still follows the address row
        title = self._one(article, "./h2")
        self.assertEqual(title.text_content().strip(), "Rechnung RE-2026-001")
        self.assertIs(row.getnext(), title)

    def test_beside_without_information_block(self):
        tree = self._render_tree(data={"no_information_block": True})
        row = self._one(tree, ADDRESS_ROW)
        children = [child.get("name") for child in row if child.get("name")]
        self.assertEqual(children, ["address", "din5008_informations"])

    def test_form_b(self):
        self._set_form("B")
        tree = self._render_tree()
        header = self._one(tree, HEADER)
        self.assertEqual(header.get("style"), "height: 45mm;")
        self.assertEqual(header.get("data-din5008-form"), "B")
        marks = header.xpath(".//div[contains(@class, 'din5008_fold_mark')]")
        self.assertEqual(
            [m.get("style") for m in marks], ["top: 105mm;", "top: 210mm;"]
        )

    def test_logo_position(self):
        self._write_config({"din5008.logo_position": "right"})
        tree = self._render_tree()
        header = self._one(tree, HEADER)
        self.assertEqual(header.get("data-din5008-logo"), "right")
        self.assertTrue(header.xpath(".//img[@class='o_company_logo_small']"))

    def test_options_disabled(self):
        self._write_config(
            {
                "din5008.sender_line": False,
                "din5008.fold_marks": False,
                "din5008.hole_mark": False,
            }
        )
        tree = self._render_tree()
        self.assertFalse(tree.xpath("//div[@class='din5008_sender_line']"))
        self.assertFalse(tree.xpath("//div[contains(@class, 'din5008_mark')]"))
        # fold marks and hole mark are switched separately
        self._write_config({"din5008.hole_mark": True})
        tree = self._render_tree()
        self.assertFalse(tree.xpath("//div[contains(@class, 'din5008_fold_mark')]"))
        self.assertTrue(tree.xpath("//div[contains(@class, 'din5008_hole_mark')]"))

    def test_sender_line_options(self):
        self._write_config(
            {
                "din5008.sender_separator": "·",
                "din5008.sender_country": "code",
                "din5008.sender_separator_gap": 1,
                "din5008.sender_separator_font_scale": 0.8,
            }
        )
        tree = self._render_tree()
        sender = self._one(tree, "//div[@class='din5008_sender_line']")
        # the address text is printed as sender line, joined by the separator
        self.assertEqual(
            sender.text_content(), "Acme GmbH · Musterstraße 1 · 12345 Berlin"
        )
        self.assertEqual(sender.get("style"), "top: 0mm;")
        separators = sender.xpath("./span[@class='din5008_sender_separator']")
        self.assertEqual(len(separators), 2)
        self.assertEqual(separators[0].get("style"), "margin: 0 1mm; font-size: 0.8em;")
        # the formatted placeholder in the address applies the country option
        self.company.company_details = (
            '<p><t t-out="object.layout_din5008_sender_line_text"/></p>'
        )
        tree = self._render_tree()
        sender = self._one(tree, "//div[@class='din5008_sender_line']")
        self.assertEqual(
            sender.text_content(), "Acme GmbH · Musterstraße 1 · DE-12345 Berlin"
        )
        self.assertEqual(
            len(sender.xpath("./span[@class='din5008_sender_separator']")), 2
        )

    def test_custom_geometry(self):
        self._write_config(
            {
                "din5008.address_offset_top": 3,
                "din5008.address_height": 50,
                "din5008.info_left": 120,
                "din5008.info_width": 80,
                "din5008.remark_zone_height": 8,
            }
        )
        tree = self._render_tree()
        article = self._one(tree, ARTICLE)
        style = self._one(article, "./style").text
        self.assertIn("margin-top: 3mm; min-height: 50mm", style)
        self.assertIn("padding-top: 13mm", style)
        self.assertIn("margin-left: 100mm; width: 80mm", style)
        sender = self._one(article, ".//div[@class='din5008_sender_line']")
        self.assertEqual(sender.get("style"), "top: 3mm;")

    def test_extension_of_standard_layout_applies(self):
        """Extensions of web.external_layout_standard apply to the DIN layout."""
        self.env["ir.ui.view"].create(
            {
                "name": "layout_din5008.test_extension",
                "type": "qweb",
                "inherit_id": self.env.ref("web.external_layout_standard").id,
                "mode": "extension",
                "arch": """
                    <xpath expr="//img[hasclass('o_company_logo_small')]"
                           position="after">
                        <span class="din5008_test_extension">EXTENSION</span>
                    </xpath>
                """,
            }
        )
        tree = self._render_tree()
        header = self._one(tree, HEADER)
        extension = self._one(header, ".//span[@class='din5008_test_extension']")
        self.assertEqual(extension.text, "EXTENSION")
        # footer lines of the base module are printed in the footer
        lines = self.env["ir.ui.view"].create(
            {
                "name": "layout_din5008.test_footer_lines",
                "type": "qweb",
                "inherit_id": self.env.ref("l10n_de_report_footer.footer_lines").id,
                "mode": "extension",
                "arch": """
                    <xpath expr="//t[@name='l10n_de_report_footer_lines']"
                           position="inside">
                        <li class="din5008_test_line">HRB 1</li>
                    </xpath>
                """,
            }
        )
        tree = self._render_tree()
        footer = self._one(tree, FOOTER)
        self._one(
            footer, ".//ul[@name='din5008_footer_legal']/li[@class='din5008_test_line']"
        )
        lines.unlink()

    def test_logo_height(self):
        tree = self._render_tree()
        logo = self._one(tree, "//img[@class='o_company_logo_small']")
        self.assertIsNone(logo.get("style"))
        self._write_config({"din5008.logo_height": 12})
        tree = self._render_tree()
        logo = self._one(tree, "//img[@class='o_company_logo_small']")
        self.assertEqual(logo.get("style"), "max-height: 12mm;")

    def test_footer_lines(self):
        """The footer lines of the base module are printed in the legal block."""
        Company = self.env["res.company"]
        if "l10n_de_widnr" not in Company._fields:
            self.skipTest("l10n_de is not installed")
        self.company.write({"l10n_de_widnr": "DE123456788-00001"})
        self._write_config({"footer.show_de_widnr": True})
        tree = self._render_tree()
        footer = self._one(tree, FOOTER)
        legal = self._one(footer, ".//ul[@name='din5008_footer_legal']")
        lines = [" ".join(li.text_content().split()) for li in legal.xpath("./li")]
        label = Company._fields["l10n_de_widnr"]._description_string(self.env)
        self.assertIn(f"{label}: DE123456788-00001", lines)
        # after the VAT number
        self.assertLess(
            lines.index(next(line for line in lines if "DE123456788" in line)),
            lines.index(f"{label}: DE123456788-00001"),
        )
