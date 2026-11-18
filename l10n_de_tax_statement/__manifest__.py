# Copyright 2019-2020 Onestein (<https://www.onestein.eu>)
# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "German VAT Statement",
    "version": "18.0.4.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Onestein, MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["account", "l10n_de"],
    "data": [
        "security/ir.model.access.csv",
        "security/tax_statement_security_rule.xml",
        "views/l10n_de_tax_statement_view.xml",
        "views/res_config_settings_view.xml",
    ],
    "maintainers": ["mt-software-de"],
}
