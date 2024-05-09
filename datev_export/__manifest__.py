# Copyright (C) 2024 Solvti sp. z o.o. (https://solvti.pl)
# Copyright (C) 2023 initOS GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Datev Export",
    "version": "16.0.1.0.1",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Guenter Selbert, Thorsten Vocks, Maciej Wichowski, Daniela Scarpa, "
    "Maria Sparenberg, initOS GmbH, Jan Sierpina, Odoo Community Association (OCA)",
    "summary": "Export invoices and refunds as xml and pdf files zipped in DATEV format.",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": [
        "account",
        "l10n_de",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
