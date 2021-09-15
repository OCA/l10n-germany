# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 Florian Kantelberg <florian.kantelberg@initos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestL10nDeToponyms(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nDeToponyms, cls).setUpClass()
        cls.wizard = cls.env['config.de.toponyms'].create({
            'name': '',
        })

    def test_import(self):
        self.wizard.with_context(max_import=10).execute()
        cities = self.env['res.city'].search([
            ('country_id', '=', self.env.ref('base.de').id)
        ])
        self.assertTrue(cities)
        self.assertTrue(cities.mapped('zip_ids'))
