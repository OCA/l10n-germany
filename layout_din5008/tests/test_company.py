# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

from ..models.layout_din5008_mixin import DIN5008_LAYOUT_KEYS

DIN5008_KEYS = [
    "din5008.informations_position",
    "din5008.logo_position",
    "din5008.logo_height",
    "din5008.address_font_scale",
    "din5008.fold_marks",
    "din5008.hole_mark",
    "din5008.sender_line",
    "din5008.sender_separator",
    "din5008.sender_separator_gap",
    "din5008.sender_separator_font_scale",
    "din5008.sender_country",
    "din5008.address_offset_top",
    "din5008.address_height",
    "din5008.remark_zone_height",
    "din5008.info_left",
    "din5008.info_width",
]


@tagged("post_install", "-at_install")
class TestCompany(TransactionCase):
    def test_defaults(self):
        company = self.env["res.company"].create({"name": "DIN Test Company"})
        self.assertFalse(company.report_layout_config)
        option = company._layout_din5008_option
        self.assertEqual(option("address_offset_top"), 0)
        self.assertEqual(option("address_height"), 45)
        self.assertEqual(option("info_left"), 125)
        self.assertEqual(option("info_width"), 75)
        self.assertEqual(option("remark_zone_height"), 0)
        self.assertEqual(option("logo_position"), "left")
        self.assertIs(option("fold_marks"), False)
        self.assertIs(option("hole_mark"), False)
        self.assertIs(option("sender_line"), True)
        self.assertEqual(option("sender_separator"), "|")
        self.assertEqual(option("sender_separator_gap"), 0)
        self.assertEqual(option("sender_separator_font_scale"), 1.0)
        self.assertEqual(option("logo_height"), 0)
        self.assertEqual(option("address_font_scale"), 1.0)
        self.assertEqual(option("sender_country"), "none")
        self.assertEqual(option("informations_position"), "beside")
        # the stored value wins over the default
        company._set_report_layout_config_value("din5008.fold_marks", value=True)
        self.assertIs(option("fold_marks"), True)

    def test_spec(self):
        Company = self.env["res.company"]
        specs = Company._get_report_layout_config_fields_by_key()
        for key in DIN5008_KEYS:
            self.assertIn(key, specs)
            self.assertEqual(specs[key]["layouts"], list(DIN5008_LAYOUT_KEYS))
        # the DIN settings are offered for the DIN layouts only; the bottom
        # margin of the base module is moved to the end of the positions tab
        for layout_key in DIN5008_LAYOUT_KEYS:
            offered = Company.get_report_layout_config_fields(layout_key)
            keys = [s["key"] for s in offered]
            self.assertEqual(
                [key for key in keys if key.startswith("din5008.")], DIN5008_KEYS
            )
            self.assertEqual(keys[-1], "page.margin_bottom")
            margin = offered[-1]
            self.assertEqual(margin["section"], "din5008_geometry")
            self.assertEqual(margin["section_label"], "Positions (mm)")
            self.assertEqual(margin["label"], "Bottom Margin")
            self.assertEqual(margin["highlight"], "footer")
            self.assertEqual(margin["type"], "integer")
        offered = Company.get_report_layout_config_fields(
            "web.external_layout_standard"
        )
        keys = [s["key"] for s in offered]
        self.assertEqual(
            [key for key in keys if not key.startswith("footer.")],
            ["page.margin_bottom"],
        )
        # other layouts keep the tab of the base module
        self.assertEqual(offered[0]["section"], "page")
        self.assertEqual(specs["page.margin_bottom"]["section"], "page")
        # the sender line options depend on the sender line switch
        self.assertEqual(
            specs["din5008.sender_separator"]["visible_if"],
            {"din5008.sender_line": True},
        )
        self.assertEqual(specs["din5008.address_height"]["highlight"], "address")
        # the separator is free text with presets
        separator = specs["din5008.sender_separator"]
        self.assertEqual(separator["type"], "char")
        self.assertEqual([o[0] for o in separator["options"]], ["|", "•", "·"])
        self.assertEqual(separator["visible_if"], {"din5008.sender_line": True})
        self.assertEqual(specs["din5008.info_left"]["highlight"], "information_block")

    def test_constraints(self):
        company = self.env.company
        for key, low, high in [
            ("din5008.address_offset_top", -10, 30),
            ("din5008.address_height", 20, 80),
            ("din5008.info_left", 105, 160),
            ("din5008.info_width", 30, 90),
            ("din5008.remark_zone_height", 0, 20),
            ("din5008.sender_separator_gap", 0, 5),
            ("din5008.sender_separator_font_scale", 0.5, 2),
            ("din5008.address_font_scale", 0.5, 2),
        ]:
            company._set_report_layout_config_value(key, value=low)
            company._set_report_layout_config_value(key, value=high)
            with self.assertRaises(ValidationError, msg=key):
                company._set_report_layout_config_value(key, value=low - 1)
            with self.assertRaises(ValidationError, msg=key):
                company._set_report_layout_config_value(key, value=high + 1)
        company._set_report_layout_config_value(
            "din5008.remark_zone_height", value=12.7
        )
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value(
                "din5008.address_height", value=45.5
            )
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value(
                "din5008.logo_position", value="top"
            )
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value("din5008.fold_marks", value=1)
        # the logo height accepts 0 (layout default) outside the range
        company._set_report_layout_config_value("din5008.logo_height", value=0)
        company._set_report_layout_config_value("din5008.logo_height", value=45)
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value("din5008.logo_height", value=3)
        # any text is accepted as separator
        company._set_report_layout_config_value("din5008.sender_separator", value="-")
        with self.assertRaises(ValidationError):
            company._set_report_layout_config_value("din5008.sender_separator", value=1)
