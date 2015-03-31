# -*- coding: utf-8 -*-
# Python source code encoding : https://www.python.org/dev/peps/pep-0263/
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2015 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
#                 Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api
from openerp.tools.translate import _
from openerp.addons.base_location_nuts.models.res_partner \
    import dict_recursive_update


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.depends('country_id')
    def _labels_get(self):
        super(ResPartner, self)._labels_get()
        if self.country_id.code == 'DE':
            self.lbl_substate = _('Government region')
            self.lbl_region = _('District')

    @api.multi
    def onchange_state(self, state_id):
        result = super(ResPartner, self).onchange_state(state_id)
        state = self.env['res.country.state'].browse(state_id)
        if state.country_id.code == 'DE':
            changes = {
                'domain': {
                    'substate': [('country_id', '=', 'DE'),
                                 ('level', '=', 3)],
                    'region': [('country_id', '=', 'DE'),
                               ('level', '=', 4)],
                },
                'value': {}
            }
            nuts_state = self.env['res.partner.nuts'].search(
                [('level', '=', 2),
                 ('state_id', '=', state_id)])
            if nuts_state:
                changes['domain']['substate'].append(
                    ('parent_id', 'in', nuts_state.ids))
            if self.substate.country_id.code != 'DE':
                changes['value']['substate'] = False
            if self.region.country_id.code != 'DE':
                changes['value']['region'] = False
            dict_recursive_update(result, changes)
        return result

    @api.onchange('substate', 'region')
    def onchange_substate_or_region(self):
        result = super(ResPartner, self).onchange_substate_or_region()
        if (self.state_id.country_id.code == 'DE' or
                self.substate.country_id.code == 'DE' or
                self.region.country_id.code == 'DE'):
            changes = {
                'domain': {
                    'substate': [('country_id', '=', 'DE'),
                                 ('level', '=', 3)],
                    'region': [('country_id', '=', 'DE'),
                               ('level', '=', 4)],
                }
            }
            if self.state_id.country_id.code == 'DE':
                nuts_state = self.env['res.partner.nuts'].search(
                    [('level', '=', 2),
                     ('state_id', '=', self.state_id.id)])
                if nuts_state:
                    changes['domain']['substate'].append(
                        ('parent_id', 'in', nuts_state.ids))
                self.country_id = self.state_id.country_id
            if self.substate.country_id.code == 'DE':
                changes['domain']['region'].append(
                    ('parent_id', '=', self.substate.id))
                self.country_id = self.substate.country_id
            if self.region.country_id.code == 'DE':
                if self.region.parent_id != self.substate:
                    self.substate = self.region.parent_id
                self.country_id = self.region.country_id
            dict_recursive_update(result, changes)
        return result
