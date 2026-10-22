# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestResPartner(BaseCommon):
    def test_function_is_translatable(self):
        field = self.env["res.partner"]._fields["function"]
        self.assertTrue(field.translate)
