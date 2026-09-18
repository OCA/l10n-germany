# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company",
                "l10n_din5008_country_indicator": "code",
                "l10n_din5008_address_separator": "pipe",
                "l10n_din5008_sender_font_factor": 1.5,
            }
        )
        cls.wizard = cls.env["base.document.layout"].create(
            {
                "company_id": cls.company.id,
            }
        )

    def test_related_fields(self):
        self.assertEqual(
            self.wizard.l10n_din5008_country_indicator,
            self.company.l10n_din5008_country_indicator,
        )
        self.assertEqual(
            self.wizard.l10n_din5008_address_separator,
            self.company.l10n_din5008_address_separator,
        )
        self.assertEqual(
            self.wizard.l10n_din5008_sender_font_factor,
            self.company.l10n_din5008_sender_font_factor,
        )

    def test_onchange_din5008_report_company_sender_address(self):
        with patch.object(
            type(self.wizard),
            "_compute_preview",
        ) as compute_preview:
            self.wizard._onchange_din5008_report_company_sender_address()

            compute_preview.assert_called_once_with()
