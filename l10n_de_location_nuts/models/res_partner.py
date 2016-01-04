# -*- coding: utf-8 -*-
# Python source code encoding : https://www.python.org/dev/peps/pep-0263/
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2015 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
#                 Antonio Espinosa <antonioea@antiun.com>
#                 Jairo Llopis <yajo.sk8@gmail.com>
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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def onchange_state(self, state_id):
        result = super(ResPartner, self).onchange_state(state_id)
        state = self.env['res.country.state'].browse(state_id)

        # Ignore non-German states
        if state.country_id.code == 'DE':
            # Substate must belong to state
            result.setdefault("domain", dict())
            self.country_id = state.country_id
            result["domain"]["substate_id"] = self._l10n_de_substate_domain()
            result["domain"]["region_id"] = self._l10n_de_region_domain()

            # Substate and region must be German
            result.setdefault("value", dict())
            if not self.env.context.get("skip_empty_substate_region"):
                if self.substate_id.country_id.code != 'DE':
                    result['value']['substate_id'] = False
                if self.region_id.country_id.code != 'DE':
                    result['value']['region_id'] = False

        return result

    @api.multi
    @api.onchange("substate_id")
    def _onchange_substate_id(self):
        """State must be substate parent, region must be substate child."""
        result = super(ResPartner, self)._onchange_substate_id()

        # Ignore non-German substates
        if self.substate_id.country_id.code == "DE":
            self.state_id = self.substate_id.parent_id.state_id
            if self.region_id.parent_id != self.substate_id:
                self.region_id = False
            result.setdefault("domain", dict())
            result["domain"]["region_id"] = self._l10n_de_region_domain()

            # Ugly hack to avoid false positives in :meth:`onchange_state`.
            # Without this, it would always empty substate and region.
            # That method definitely needs to be ported to new api.
            # See https://github.com/odoo/odoo/pull/10285.
            self.env.context = self.with_context(
                skip_empty_substate_region=True).env.context

        return result

    @api.multi
    @api.onchange("region_id")
    def _onchange_region_id(self):
        result = super(ResPartner, self)._onchange_region_id()

        # Ignore non-German regions
        if self.region_id.country_id.code == "DE":
            self.substate_id = self.region_id.parent_id

        return result

    @api.multi
    @api.onchange("country_id")
    def _onchange_country_id(self):
        """Fix domains for Germany."""
        result = super(ResPartner, self)._onchange_country_id()

        # Ignore if country is not Germany
        if self.country_id.code == "DE":
            result.setdefault("domain", dict())
            result["domain"]["substate_id"] = self._l10n_de_substate_domain()
            result["domain"]["region_id"] = self._l10n_de_region_domain()

        return result

    @api.multi
    def _l10n_de_substate_domain(self):
        """Substate must belong to state if available."""
        nuts_state = self.env['res.partner.nuts'].search(
            [('level', '=', self.country_id.state_level),
             ('state_id', '=', self.state_id.id)])

        domain = [
            ("country_id", "=", self.country_id.id),
            ("level", "=", self.country_id.substate_level),
        ]

        if self.state_id and nuts_state:
            domain.append(("parent_id", "in", nuts_state.ids))

        return domain

    @api.multi
    def _l10n_de_region_domain(self):
        """Region must belong to substate if available."""
        domain = [
            ("country_id", "=", self.country_id.id),
            ("level", "=", self.country_id.region_level),
        ]

        if self.substate_id:
            domain.append(("parent_id", "=", self.substate_id.id))

        return domain
