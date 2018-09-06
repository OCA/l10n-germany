# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 IT IS AG <oca@itis.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools
import os


class ConfigDeToponyms(models.TransientModel):
    _name = 'config.de.toponyms'
    _inherit = 'res.config.installer'

    name = fields.Char('Name', size=64)

    @api.model
    def create_zipcodes(self):
        """Import spanish zipcodes information through an XML file."""
        file_name = 'l10n_de_toponyms_zipcodes.xml'
        path = os.path.join('l10n_de_toponyms', 'wizard', file_name)
        with tools.file_open(path) as fp:
            tools.convert_xml_import(self.env.cr, 'l10n_de_toponyms', fp, {},
                                     'init', noupdate=True)
        return True

    @api.multi
    def execute(self):
        res = super(ConfigDeToponyms, self).execute()
        wizard_obj = self.env['better.zip.geonames.import']
        country_es = self.env['res.country'].search([('code', '=', 'DE')])
        wizard = wizard_obj.create({'country_id': country_es.id})
        wizard.run_import()
        return res

    @api.multi
    def execute_local(self):  # pragma: no cover
        self.create_zipcodes()
