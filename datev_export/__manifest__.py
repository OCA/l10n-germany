# Copyright (C) 2023 initOS GmbH
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Datev Export",
    "version": "13.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "Guenter Selbert, Thorsten Vocks, Maciej Wichowski, Daniela Scarpa, "
    "Maria Sparenberg, initOS GmbH, Odoo Community Association (OCA)",
    "summary": "Export invoices and refunds as xml and pdf files zipped in DATEV format.",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["account", "l10n_de"],
    "data": ["views/res_config_settings_views.xml"],
    "installable": True,
}
