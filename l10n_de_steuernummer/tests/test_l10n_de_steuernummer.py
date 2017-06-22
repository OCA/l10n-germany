# -*- coding: utf-8 -*-
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import exceptions
from odoo.tests import common


class TestL10nDeSteuerNummer(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nDeSteuerNummer, cls).setUpClass()
        cls.env.user.company_id.vat_check_vies = False
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test',
        })

    def test_correct_steuernummer(self):
        """VAT with 11 chars that doesn't throw error."""
        self.partner.vat = 'DE12345678901'

    def test_incorrect_steuernummer(self):
        """VAT with 9 chars that throws an error."""
        with self.assertRaises(exceptions.ValidationError):
            self.partner.vat = 'DE123456789'
