# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestDin5008Base(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.paperformat = cls.env.ref("l10n_din5008.paperformat_euro_din_a")
        cls.layout = cls.env.ref("l10n_din5008.external_layout_din5008")

    def test_din5008_css_configuration(self):
        self.company.write(
            {
                "paperformat_id": self.paperformat.id,
                "external_report_layout_id": self.layout.id,
                "l10n_din5008_config": {
                    "header": {
                        "company_logo_size": {"type_a": 35},
                        "company_logo_position": {"type_a": "left"},
                        "company_logo_lr_margin": 10,
                        "company_logo_bt_margin": 15,
                    },
                    "receiver": {"font_factor": 0.9},
                    "sender": {
                        "font_factor": 0.7,
                        "address_margin_left": 1.0,
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
        rendered = " ".join(str(rendered).split())

        for expected in (
            "max-height: 35mm",
            "margin: 15mm 10mm",
            "float: left",
            "font-size: 0.9em",
            "font-size: 0.7em",
            "margin-left: 1.0mm",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
