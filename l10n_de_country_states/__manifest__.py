# -*- coding: utf-8 -*-
# Copyright 2015 Nikolina Todorova <nikolina.todorova@initos.com>
# Copyright 2015 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'German Country States',
    'category': 'Localisation/Europe',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'initOS GmbH & Co. KG, '
              'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'https://odoo-community.org/',
    'depends': [
        'base_country_state_translatable',
    ],
    'data': [
        'data/res_country_states.xml'
    ],
    'installable': True,
}
