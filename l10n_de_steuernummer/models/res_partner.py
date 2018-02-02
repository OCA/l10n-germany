# Copyright 2015 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import api, models

try:
    import vatnumber
except ImportError:
    vatnumber = None


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def check_vat_de(self, vat):
        res = False
        if getattr(vatnumber, 'check_vat_de', None):
            res = vatnumber.check_vat_de(vat)
        if not res:
            # This vat is not a Steuer-IdNr., so if it is 10 or 11 digit
            # length then we can assume that this is a old Steuernummer
            vat = re.sub(r'[^0-9]', '', vat)
            return 10 <= len(vat) <= 11
        return res
