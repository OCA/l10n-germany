# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Define German specific configuration in res.country."""
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        germany = env.ref('base.de')
        _logger.info('Setting Germany NUTS configuration')
        spain.write({
            'state_label': 'State',
            'substate_label': 'District',
            'region_label': 'Government region',
            'state_level': 2,
            'substate_level': 3,
            'region_level': 4,
        })
