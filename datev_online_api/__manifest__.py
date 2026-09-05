# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "DATEV Online API",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "summary": "Base module for the DATEV Online API which handles authentication and "
    "offers the framework for all modules built on top",
    "depends": [
        "datev_export",
        "web",
    ],
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
