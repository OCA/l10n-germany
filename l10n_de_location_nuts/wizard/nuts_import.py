# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2015 Tecnativa - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class NutsImport(models.TransientModel):
    _inherit = "nuts.import"
    _de_state_map = {
        # BADEN-WÜRTTEMBERG
        "DE1": "base.state_de_bw",
        # BAYERN
        "DE2": "base.state_de_by",
        # BERLIN
        "DE3": "base.state_de_be",
        # BRANDENBURG
        "DE4": "base.state_de_bb",
        # BREMEN
        "DE5": "base.state_de_hb",
        # HAMBURG
        "DE6": "base.state_de_hh",
        # HESSEN
        "DE7": "base.state_de_he",
        # MECKLENBURG-VORPOMMERN
        "DE8": "base.state_de_mv",
        # NIEDERSACHSEN
        "DE9": "base.state_de_ni",
        # NORDRHEIN-WESTFALEN
        "DEA": "base.state_de_nw",
        # RHEINLAND-PFALZ
        "DEB": "base.state_de_rp",
        # SAARLAND
        "DEC": "base.state_de_sl",
        # SACHSEN
        "DED": "base.state_de_sn",
        # SACHSEN-ANHALT
        "DEE": "base.state_de_st",
        # SCHLESWIG-HOLSTEIN
        "DEF": "base.state_de_sh",
        # THÜRINGEN
        "DEG": "base.state_de_th",
        # EXTRA-REGIO NUTS 1
        "DEZ": False,
    }

    def _create_partner_nuts(self, nuts_data):
        nuts_ids = super()._create_partner_nuts(nuts_data)
        for nut in nuts_ids:
            if self._de_state_map.get(nut.code, False):
                nut.state_id = self.env.ref(self._de_state_map[nut.code])
        return nuts_ids
