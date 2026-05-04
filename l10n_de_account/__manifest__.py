# Copyright 2026 elego Software Solutions GmbH - Yu Weng
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Accounting for Germany",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Account",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "summary": "Change the menu from Invoicing to Accounting",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_menuitem.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "post_init_hook": "_l10n_de_account_post_init",
}
