# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.addons.base.tests.common import BaseCommon


class TestBaseDocumentLayout(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Representative",
            }
        )
        cls.role = cls.env["res.company.representative.role"].create(
            {
                "name": "Test CEO",
            }
        )
        cls.env.company.representatives = [
            (
                0,
                0,
                {
                    "partner_id": cls.partner.id,
                    "representative_role_id": cls.role.id,
                },
            )
        ]

    def test_representatives_are_available_in_layout(self):
        layout = self.env["base.document.layout"].create(
            {
                "company_id": self.env.company.id,
            }
        )
        self.assertEqual(
            layout.representatives,
            self.env.company.representatives,
        )

    def test_get_representatives(self):
        layout = self.env["base.document.layout"].create(
            {
                "company_id": self.env.company.id,
            }
        )
        representatives = layout.get_representatives()
        self.assertEqual(len(representatives), 1)
        self.assertEqual(
            representatives[0]["partner"],
            self.partner.name,
        )
        self.assertEqual(
            representatives[0]["role"],
            self.role.name,
        )

    def test_show_representatives(self):
        self.env.company.din_5008_show_representatives = True
        layout = self.env["base.document.layout"].create(
            {
                "company_id": self.env.company.id,
            }
        )
        self.assertTrue(layout.din_5008_show_representatives)
        layout.din_5008_show_representatives = False
        self.assertFalse(self.env.company.din_5008_show_representatives)

    def test_onchange_show_representatives(self):
        layout = self.env["base.document.layout"].create(
            {
                "company_id": self.env.company.id,
            }
        )
        with patch.object(
            type(layout),
            "_compute_preview",
        ) as compute_preview:
            layout._onchange_din5008_report_show_representatives()

        compute_preview.assert_called_once_with()
