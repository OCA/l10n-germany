# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestDin5008Footer(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.paperformat = cls.env.ref("l10n_din5008.paperformat_euro_din_a")
        cls.layout = cls.env.ref("l10n_din5008.external_layout_din5008")

    def setUp(self):
        super().setUp()
        self.company.paperformat_id = self.paperformat
        self.company.l10n_din5008_config = {}

    def _render_footer(self, config):
        self.company.l10n_din5008_config = config
        return self.env["ir.qweb"]._render(
            "l10n_din5008_report_base_footer.external_layout_din5008_config_inherit_footer",
            {
                "company": self.company,
                "is_din_paperformat": True,
                "din5008_config": config,
                "o": False,
                "env": self.env,
            },
        )

    def test_din5008_footer_company_details(self):
        self.company.write(
            {
                "phone": "0123456789",
                "email": "info@example.com",
                "website": "https://example.com",
                "vat": "DE123456789",
                "company_registry": "HRB 12345",
            }
        )
        config = {
            "footer": {
                "fa_contact_preset": True,
                "show_vat": True,
                "show_company_registry": True,
            }
        }
        rendered = str(self._render_footer(config))

        for expected in (
            "0123456789",
            "info@example.com",
            "https://example.com",
            "DE123456789",
            "HRB 12345",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)

    def test_din5008_footer_representatives(self):
        # representative = self.env["res.partner"].create({
        #    "name": "Max Mustermann",
        #    # "function": {"en_US": "Managing Director"},
        # })
        representative = self.env["res.partner"].create(
            {"name": "Max Mustermann", "function": "Managing Director"}
        )
        config = {
            "footer": {
                "show_representatives": True,
                "representatives": [{"partner_id": representative.id}],
            }
        }
        rendered = str(self._render_footer(config))
        self.assertIn("Max Mustermann", rendered)
        self.assertIn("Managing Director", rendered)
        config["footer"]["show_representatives"] = False
        rendered = str(self._render_footer(config))
        self.assertNotIn("Max Mustermann", rendered)

    def test_din5008_footer_css_configuration(self):
        self.company.write(
            {
                "paperformat_id": self.paperformat.id,
                "external_report_layout_id": self.layout.id,
                "l10n_din5008_config": {
                    "footer": {
                        "line_height": 1.7,
                        "separator_spacing": 2.4,
                        "font_scale_factor": 1.2,
                        "table_width_pattern": "20,30,25,25",
                    },
                },
            }
        )

        rendered = str(
            self.env["ir.qweb"]._render(
                "web.styles_company_report",
                {"company_ids": self.company},
            )
        )

        for expected in ("1.7em", "2.4mm", "1.2em", "20%", "30%"):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
