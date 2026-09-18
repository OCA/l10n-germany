# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestResCompany(BaseCommon):
    def test_margin_bottom_invalid_below_minimum(self):
        with self.assertRaises(ValidationError):
            self.env.company.l10n_din5008_margin_bottom = 4

    def test_margin_bottom_invalid_above_maximum(self):
        with self.assertRaises(ValidationError):
            self.env.company.l10n_din5008_margin_bottom = 61

    def test_margin_bottom_minimum_value(self):
        self.env.company.l10n_din5008_margin_bottom = 5
        self.assertEqual(
            self.env.company.l10n_din5008_margin_bottom,
            5,
        )

    def test_margin_bottom_maximum_value(self):
        self.env.company.l10n_din5008_margin_bottom = 60
        self.assertEqual(
            self.env.company.l10n_din5008_margin_bottom,
            60,
        )
