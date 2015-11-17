# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

import re
from openerp import models

try:
    import vatnumber
except ImportError:
    vatnumber = None


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def check_vat_de(self, vat):
        res = False
        official = getattr(vatnumber, 'check_vat_de', None)
        if official:
            res = official(vat)
        if not res:
            # This vat is not a Steue-IdNr., so if it is 10 or 11 digit length
            # then we can assume that this is a old Steuernummer
            vat = re.sub(r'[^0-9]', '', vat)
            if len(vat) >= 10 and len(vat) <= 11:
                res = True
        return res
