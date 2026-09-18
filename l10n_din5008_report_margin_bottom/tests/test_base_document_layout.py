# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    def test_margin_bottom_related_to_company(self):
        company = self.env.company
        company.l10n_din5008_margin_bottom = 40
        layout = self.env["base.document.layout"].new(
            {
                "company_id": company.id,
            }
        )
        self.assertEqual(
            layout.l10n_din5008_margin_bottom,
            40,
        )
