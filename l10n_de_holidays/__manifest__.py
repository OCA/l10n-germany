# Copyright 2018 elego Software Solutions GmbH - Yu Weng
# Copyright 2018 initOS GmbH - Nikolina Todorova
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Holidays for Germany",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": [
        "calendar_public_holiday",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/calendar_public_holiday_generator_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
