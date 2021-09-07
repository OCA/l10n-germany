# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 IT IS AG <oca@itis.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ConfigDeToponyms(models.TransientModel):
    _name = "config.de.toponyms"
    _inherit = "res.config.installer"
    _description = "config de toponyms"

    name = fields.Char("Name", size=64)

    def execute(self):
        res = super(ConfigDeToponyms, self).execute()
        wizard_obj = self.env["city.zip.geonames.import"]
        country_es = self.env["res.country"].search([("code", "=", "DE")])
        wizard = wizard_obj.create({"country_id": country_es.id})
        wizard.run_import()
        return res
