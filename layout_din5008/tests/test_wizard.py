# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged

from .common import LayoutDin5008Common


@tagged("post_install", "-at_install")
class TestWizard(LayoutDin5008Common, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_din5008()
        cls.report_layout_a = cls.env.ref("layout_din5008.report_layout_din5008_a")
        cls.report_layout_b = cls.env.ref("layout_din5008.report_layout_din5008_b")
        cls.report_layout_standard = cls.env.ref("web.report_layout_standard")
        cls.paperformat_euro = cls.env.ref("base.paperformat_euro")

    @staticmethod
    def _offered_keys(wizard):
        return [spec["key"] for spec in wizard.report_layout_config_fields]

    @staticmethod
    def _offered_section(wizard, key):
        return next(
            spec["section"]
            for spec in wizard.report_layout_config_fields
            if spec["key"] == key
        )

    def test_layout_selection_sets_paperformat(self):
        self.company.write(
            {
                "external_report_layout_id": self.env.ref(
                    "web.external_layout_standard"
                ).id,
                "paperformat_id": self.paperformat_euro.id,
            }
        )
        with Form(self.env["base.document.layout"]) as wizard:
            self.assertNotIn("din5008.fold_marks", self._offered_keys(wizard))
            self.assertEqual(
                self._offered_section(wizard, "page.margin_bottom"), "page"
            )
            wizard.report_layout_id = self.report_layout_a
            self.assertIn("din5008.fold_marks", self._offered_keys(wizard))
            self.assertEqual(wizard.paperformat_id, self.paperformat_a)
            # the bottom margin joins the positions tab of the DIN layouts
            self.assertEqual(
                self._offered_section(wizard, "page.margin_bottom"), "din5008_geometry"
            )
            wizard.report_layout_id = self.report_layout_b
            self.assertEqual(wizard.paperformat_id, self.paperformat_b)
            wizard.report_layout_id = self.report_layout_standard
            self.assertEqual(self._offered_keys(wizard), ["page.margin_bottom"])
            self.assertEqual(
                self._offered_section(wizard, "page.margin_bottom"), "page"
            )
            # the paper format of another layout is not touched
            self.assertEqual(wizard.paperformat_id, self.paperformat_b)

    def test_save_writes_company_config(self):
        with Form(self.env["base.document.layout"]) as wizard:
            wizard.report_layout_id = self.report_layout_b
            self._set_wizard_config(
                wizard,
                {
                    "din5008.fold_marks": False,
                    "page.margin_bottom": 40,
                    "din5008.remark_zone_height": 12.7,
                    "din5008.logo_position": "right",
                    "din5008.informations_position": "below",
                },
            )
        self.assertEqual(self.company.external_report_layout_id, self.layout_b)
        self.assertEqual(self.company.paperformat_id, self.paperformat_b)
        option = self.company._layout_din5008_option
        self.assertIs(option("fold_marks"), False)
        self.assertEqual(self.company._get_report_footer_margin_bottom(), 40)
        self.assertEqual(option("remark_zone_height"), 12.7)
        self.assertEqual(option("logo_position"), "right")
        self.assertEqual(option("informations_position"), "below")
        # settings not touched by the wizard are kept
        self.assertIs(option("hole_mark"), True)

    def test_invalid_values_rejected(self):
        with self.assertRaises(ValidationError):
            with Form(self.env["base.document.layout"]) as wizard:
                wizard.report_layout_id = self.report_layout_a
                self._set_wizard_config(wizard, {"page.margin_bottom": 70})
        with self.assertRaises(ValidationError):
            with Form(self.env["base.document.layout"]) as wizard:
                self._set_wizard_config(wizard, {"din5008.info_left": 200})

    def test_preview(self):
        with Form(self.env["base.document.layout"]) as wizard:
            self.assertEqual(wizard.report_layout_id, self.report_layout_a)
            preview = wizard.preview
            self.assertIn("din5008_sender_line", preview)
            self.assertIn("Acme GmbH | Musterstraße 1 | 12345 Berlin", preview)
            self.assertIn("o_layout_din5008", preview)
            self.assertIn('style="height: 27mm;"', preview)
            # "beside" is the default: the information block is relocated
            self.assertIn('class="din5008_informations"', preview)
            self.assertLess(
                preview.index('class="din5008_informations"'),
                preview.index('id="informations"'),
            )

            self._set_wizard_config(wizard, {"din5008.informations_position": "below"})
            self.assertNotIn('class="din5008_informations"', wizard.preview)

            self._set_wizard_config(wizard, {"din5008.sender_line": False})
            self.assertNotIn('class="din5008_sender_line"', wizard.preview)

            wizard.report_layout_id = self.report_layout_b
            self.assertIn('style="height: 45mm;"', wizard.preview)

            self._set_wizard_config(wizard, {"din5008.logo_position": "right"})
            self.assertIn('data-din5008-logo="right"', wizard.preview)

            # the sender line placeholder in the address follows the unsaved
            # format settings of the wizard
            self._set_wizard_config(wizard, {"din5008.sender_line": True})
            wizard.company_details = (
                '<p><t t-out="object.layout_din5008_sender_line_text"/></p>'
            )
            self._set_wizard_config(
                wizard,
                {
                    "din5008.sender_separator": "bullet",
                    "din5008.sender_country": "code",
                },
            )
            self.assertIn(
                "Acme GmbH • Musterstraße 1 • DE-12345 Berlin", wizard.preview
            )
            self.assertEqual(
                self.company.layout_din5008_sender_line_text,
                "Acme GmbH | Musterstraße 1 | 12345 Berlin",
            )
        # saved: the stored placeholder follows the new settings
        self.assertEqual(
            self.company.layout_din5008_sender_line_text,
            "Acme GmbH • Musterstraße 1 • DE-12345 Berlin",
        )
