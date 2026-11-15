# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "German VAT Statement ERiC",
    "summary": "Send the German VAT Statement to ELSTER with ERiC",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "development_status": "Alpha",
    "depends": ["l10n_de_tax_statement"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "wizards/l10n_de_tax_statement_eric_send_view.xml",
    ],
    "maintainers": ["mt-software-de"],
}
