# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestResCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

    def test_sender_font_factor_lower_boundary(self):
        self.company.write({"l10n_din5008_sender_font_factor": 0.5})
        self.assertEqual(
            self.company.l10n_din5008_sender_font_factor,
            0.5,
        )

    def test_sender_font_factor_upper_boundary(self):
        self.company.write({"l10n_din5008_sender_font_factor": 1.5})
        self.assertEqual(
            self.company.l10n_din5008_sender_font_factor,
            1.5,
        )

    def test_sender_font_factor_below_minimum(self):
        with self.assertRaisesRegex(
            ValidationError,
            "The company sender font scale must be between 0.5 and 1.5.",
        ):
            self.company.write({"l10n_din5008_sender_font_factor": 0.49})

    def test_sender_font_factor_above_maximum(self):
        with self.assertRaisesRegex(
            ValidationError,
            "The company sender font scale must be between 0.5 and 1.5.",
        ):
            self.company.write({"l10n_din5008_sender_font_factor": 1.51})
