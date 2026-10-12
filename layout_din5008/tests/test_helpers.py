# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from markupsafe import Markup

from odoo.tests import TransactionCase, tagged

from .common import LayoutDin5008Common


@tagged("post_install", "-at_install")
class TestHelpers(LayoutDin5008Common, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_din5008()

    def test_sender_line_from_address(self):
        # the address text of the layout, joined into one line
        self.assertEqual(
            self.company._layout_din5008_sender_line(),
            "Acme GmbH | Musterstraße 1 | 12345 Berlin",
        )
        self._write_config({"din5008.sender_separator": "bullet"})
        self.company.company_details = "<p>Acme GmbH</p><p></p><p>Berlin</p>"
        self.assertEqual(
            self.company._layout_din5008_sender_line(), "Acme GmbH • Berlin"
        )
        # placeholders are rendered
        self.company.company_details = (
            '<p><t t-out="object.layout_din5008_sender_line_text"/><br/>'
            '<t t-out="object.phone"/></p>'
        )
        self.company.phone = "+49 30 1"
        self.assertEqual(
            self.company._layout_din5008_sender_line(),
            "Acme GmbH • Musterstraße 1 • 12345 Berlin • +49 30 1",
        )
        # without address text the formatted company address is printed
        self.company.company_details = False
        self.assertEqual(
            self.company._layout_din5008_sender_line(),
            "Acme GmbH • Musterstraße 1 • 12345 Berlin",
        )

    def test_sender_line_text_field(self):
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH | Musterstraße 1 | 12345 Berlin",
        )
        self._write_config({"din5008.sender_separator": "middot"})
        self.company.partner_id.street2 = "Aufgang B"
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH · Musterstraße 1 · Aufgang B · 12345 Berlin",
        )
        # stored, hence searchable and offered by the placeholder picker
        self.assertTrue(self.company._fields["layout_din5008_sender_line_text"].store)
        self.assertTrue(
            self.env["res.company"].search(
                [("layout_din5008_sender_line_text", "ilike", "Aufgang B")]
            )
        )
        # usable as placeholder in the layout texts, also for restricted users;
        # the placeholder picker calls the whitelist on the model (call_kw)
        from odoo.service.model import call_kw

        self.assertIn(
            "object.layout_din5008_sender_line_text",
            call_kw(self.env["res.company"], "mail_allowed_qweb_expressions", [], {}),
        )
        self.company.report_footer = (
            '<p><t t-out="object.layout_din5008_sender_line_text"/></p>'
        )
        self.assertIn(
            "Acme GmbH · Musterstraße 1 · Aufgang B · 12345 Berlin",
            self.company._render_report_footer(),
        )

    def test_sender_line_country(self):
        self._write_config({"din5008.sender_country": "code"})
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH | Musterstraße 1 | DE-12345 Berlin",
        )
        self._write_config({"din5008.sender_country": "name"})
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH | Musterstraße 1 | 12345 Berlin | "
            + self.env.ref("base.de").name,
        )
        # no country on the partner: nothing is added
        self.company.partner_id.country_id = False
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH | Musterstraße 1 | 12345 Berlin",
        )
        self._write_config({"din5008.sender_country": "code"})
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH | Musterstraße 1 | 12345 Berlin",
        )

    def test_geometry(self):
        geometry = self.company._layout_din5008_geometry("A")
        self.assertEqual(geometry["header"], "height: 27mm;")
        self.assertEqual(geometry["fold_marks"], ["top: 87mm;", "top: 192mm;"])
        self.assertEqual(geometry["hole_mark"], "top: 148.5mm;")
        self.assertEqual(geometry["sender_line"], "top: 0mm;")
        self.assertIn("min-height: 45mm", geometry["company_css"])
        self.assertIn("padding-top: 5mm", geometry["company_css"])
        self.assertIn("margin-left: 105mm; width: 75mm", geometry["company_css"])
        self.assertIn(
            self.company._layout_din5008_scope_class(), geometry["company_css"]
        )

        geometry = self.company._layout_din5008_geometry("B")
        self.assertEqual(geometry["header"], "height: 45mm;")
        self.assertEqual(geometry["fold_marks"], ["top: 105mm;", "top: 210mm;"])

        self._write_config(
            {
                "din5008.address_offset_top": 5,
                "din5008.address_height": 50,
                "din5008.info_left": 130,
                "din5008.info_width": 60,
                "din5008.remark_zone_height": 12.7,
            }
        )
        geometry = self.company._layout_din5008_geometry("A")
        self.assertEqual(geometry["sender_line"], "top: 5mm;")
        self.assertIn("padding-top: 17.7mm", geometry["company_css"])
        self.assertIn("margin-top: 5mm; min-height: 50mm", geometry["company_css"])
        self.assertIn("margin-left: 110mm; width: 60mm", geometry["company_css"])

    def test_relocate_informations(self):
        address = Markup(
            '<div class="address row mb-4"><div name="address">Max</div>'
            '<div name="information_block" class="col-6">Ship</div></div>'
        )
        body = Markup(
            '<div class="page">before<div id="informations" class="row">'
            "<div class='col'><strong>Datum</strong><div>1.1.</div></div>"
            "</div>after<table><tr><td>Zeile</td></tr></table></div>"
        )
        new_address, new_body = self.company._layout_din5008_relocate_informations(
            address, body
        )
        self.assertIsInstance(new_address, Markup)
        self.assertIsInstance(new_body, Markup)
        self.assertNotIn('id="informations"', new_body)
        self.assertIn("before", new_body)
        self.assertIn("after", new_body)
        self.assertIn("<td>Zeile</td>", new_body)
        self.assertIn('class="din5008_informations"', new_address)
        self.assertIn('id="informations"', new_address)
        self.assertIn("<strong>Datum</strong>", new_address)
        # the information block stays before the relocated block
        self.assertLess(
            new_address.index("information_block"),
            new_address.index("din5008_informations"),
        )

    def test_relocate_informations_untouched(self):
        address = Markup('<div class="address row"><div name="address">Max</div></div>')
        body = Markup("<div class='page'>Umlaute äöü &amp; more</div>")
        new_address, new_body = self.company._layout_din5008_relocate_informations(
            address, body
        )
        self.assertEqual(new_address, address)
        self.assertEqual(new_body, body)
        # no address row: nothing is moved either
        body = Markup('<div class="page"><div id="informations">x</div></div>')
        new_address, new_body = self.company._layout_din5008_relocate_informations(
            Markup('<div class="oe_structure"></div>'), body
        )
        self.assertEqual(new_body, body)
        self.assertNotIn("din5008_informations", new_address)

    def test_relocate_informations_only_first(self):
        address = Markup('<div class="address row"><div name="address">Max</div></div>')
        body = Markup(
            '<div id="informations">first</div><p>tail</p>'
            '<div id="informations">second</div>'
        )
        new_address, new_body = self.company._layout_din5008_relocate_informations(
            address, body
        )
        self.assertIn("first", new_address)
        self.assertNotIn("second", new_address)
        self.assertIn("second", new_body)
        self.assertIn("<p>tail</p>", new_body)
