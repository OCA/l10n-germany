# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class NutsImport(models.TransientModel):
    _inherit = 'nuts.import'
    _de_state_map = {
        # BADEN-WÜRTTEMBERG
        'DE1': 'l10n_de_country_states.res_country_state_BW',
        # BAYERN
        'DE2': 'l10n_de_country_states.res_country_state_BY',
        # BERLIN
        'DE3': 'l10n_de_country_states.res_country_state_BE',
        # BRANDENBURG
        'DE4': 'l10n_de_country_states.res_country_state_BB',
        # BREMEN
        'DE5': 'l10n_de_country_states.res_country_state_HB',
        # HAMBURG
        'DE6': 'l10n_de_country_states.res_country_state_HH',
        # HESSEN
        'DE7': 'l10n_de_country_states.res_country_state_HE',
        # MECKLENBURG-VORPOMMERN
        'DE8': 'l10n_de_country_states.res_country_state_MV',
        # NIEDERSACHSEN
        'DE9': 'l10n_de_country_states.res_country_state_NI',
        # NORDRHEIN-WESTFALEN
        'DEA': 'l10n_de_country_states.res_country_state_NW',
        # RHEINLAND-PFALZ
        'DEB': 'l10n_de_country_states.res_country_state_RP',
        # SAARLAND
        'DEC': 'l10n_de_country_states.res_country_state_SL',
        # SACHSEN
        'DED': 'l10n_de_country_states.res_country_state_SN',
        # SACHSEN-ANHALT
        'DEE': 'l10n_de_country_states.res_country_state_ST',
        # SCHLESWIG-HOLSTEIN
        'DEF': 'l10n_de_country_states.res_country_state_SH',
        # THÜRINGEN
        'DEG': 'l10n_de_country_states.res_country_state_TH',
        # EXTRA-REGIO NUTS 1
        'DEZ': False,
    }

    @api.model
    def state_mapping(self, data, node):
        mapping = super(NutsImport, self).state_mapping(data, node)
        level = data.get('level', 0)
        code = data.get('code', '')
        if self._current_country.code == 'DE' and level == 2:
            toponyms = self._de_state_map.get(code, False)
            if toponyms:
                state = self.env.ref(toponyms)
                if state:
                    mapping['state_id'] = state.id
        return mapping
