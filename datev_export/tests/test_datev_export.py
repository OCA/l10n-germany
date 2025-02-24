# Copyright (C) 2023 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestResCompany(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Test Company",
                "datev_consultant_number": "12345678",
                "datev_client_number": "12345",
            }
        )

    def test_datev_fields(self):
        """Test that datev fields are correctly stored in res.company."""
        self.assertEqual(self.company.datev_consultant_number, "12345678")
        self.assertEqual(self.company.datev_client_number, "12345")

    def test_datev_fields_in_config_settings(self):
        """Test that datev fields are accessible via res.config.settings."""
        config = self.env["res.config.settings"].create(
            {
                "datev_consultant_number": "87654321",
                "datev_client_number": "54321",
            }
        )
        self.assertEqual(config.datev_consultant_number, "87654321")
        self.assertEqual(config.datev_client_number, "54321")
