# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestL10nDeSteuerNummer(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nDeSteuerNummer, cls).setUpClass()
        cls.env.user.company_id.vat_check_vies = False
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test',
            'country_id': 57
        })

    def test_correct_steuernummer(self):
        """VAT with 11 chars that doesn't throw error."""
        self.partner.vat = 'DE12345678901'
