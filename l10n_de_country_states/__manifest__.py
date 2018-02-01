# Copyright 2015 Nikolina Todorova <nikolina.todorova@initos.com>
# Copyright 2015 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 David Vidal <david.vidal@tecnativa.com>
# Copyright 2018 Rami Alwafaie <rami.alwafaie@initos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'German Country States',
    'category': 'Localisation/Europe',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'initOS GmbH'
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
