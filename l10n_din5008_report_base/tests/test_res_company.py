# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestResCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def setUp(self):
        super().setUp()
        self.company.l10n_din5008_config = {}

    def test_get_din5008_config(self):
        config = {"page": {"margin_bottom": 55.0}, "marks": {"fold_marker": True}}
        self.company.l10n_din5008_config = config
        self.assertEqual(self.company._get_din5008_config(), config)

    def test_get_din5008_config_empty(self):
        self.company.l10n_din5008_config = False
        self.assertEqual(self.company._get_din5008_config(), {})

    def test_get_din5008_config_value(self):
        self.company.l10n_din5008_config = {
            "page": {"margin_bottom": 55.0},
            "marks": {"fold_marker": True},
        }
        self.assertEqual(
            self.company._get_din5008_config_value("page", "margin_bottom"), 55.0
        )
        self.assertTrue(self.company._get_din5008_config_value("marks", "fold_marker"))

    def test_get_din5008_config_value_default(self):
        self.company.l10n_din5008_config = {"page": 10}
        self.assertEqual(
            self.company._get_din5008_config_value(
                "page", "margin_bottom", default=40.0
            ),
            40.0,
        )
        self.assertEqual(
            self.company._get_din5008_config_value(
                "marks", "fold_marker", default=True
            ),
            True,
        )

    def test_set_din5008_config_value(self):
        self.company._set_din5008_config_value("page", "margin_bottom", value=55.0)
        self.assertEqual(
            self.company.l10n_din5008_config["page"]["margin_bottom"], 55.0
        )

    def test_set_din5008_config_value_preserves_existing_values(self):
        self.company.l10n_din5008_config = {
            "page": {"margin_bottom": 40.0},
            "marks": {"fold_marker": True},
        }
        self.company._set_din5008_config_value("page", "margin_bottom", value=55.0)
        self.assertEqual(
            self.company.l10n_din5008_config,
            {"page": {"margin_bottom": 55.0}, "marks": {"fold_marker": True}},
        )

    def test_set_din5008_config_value_without_keys(self):
        with self.assertRaisesRegex(ValueError, "At least one key is required."):
            self.company._set_din5008_config_value(value=55.0)
