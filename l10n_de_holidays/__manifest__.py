# Copyright 2018 elego Software Solutions GmbH - Yu Weng
# Copyright 2018 initOS GmbH - Nikolina Todorova
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": 'Holidays for Germany',
    "version": '12.0.1.0.0',
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": [
        "hr_holidays_public",
    ],
    'data': [
        'wizards/hr_holidays_public_generator_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}
