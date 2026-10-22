# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT (<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestResCompany(BaseCommon):
    def test_get_din5008_optional_field_existing(self):
        self.company = self.env.company
        self.assertEqual(
            self.company._get_din5008_optional_field("name"), self.company.name
        )

    def test_get_din5008_optional_field_missing(self):
        self.assertFalse(self.company._get_din5008_optional_field("non_existing_field"))
