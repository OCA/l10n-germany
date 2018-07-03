# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Germany - Postal codes (ZIP) list',
    'summary': 'Provides all German postal codes for auto-completion',
    'version': '11.0.1.0.0',
    'category': 'Localisation/Europe',
    'licence': 'AGPL-3',
    'depends': [
        'base',
        'base_location',
        'l10n_de_country_states'
    ],
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'data': [
        'data/l10n_de_zip.xml'
    ],
    'installable': True,
}
