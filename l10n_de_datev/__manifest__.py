# Copyright 2022 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "DATEV",
    "summary": "Export Data for DATEV",
    "version": "12.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-germany",
    "author": "Hunki Enterprises BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account_fiscal_year",
        "date_range",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/l10n_de_datev_export.xml",
        "views/res_company.xml",
    ],
}
