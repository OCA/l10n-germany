# Copyright 2025 Maik Derstappen (https://derico.de)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Germany - Invoice Labor Cost Disclosure (§35a EStG)",
    "summary": "Separate labor cost disclosure on invoices for §35a EStG tax deduction",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "Ole Jancke, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["account"],
    "data": [
        "views/product_template_views.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
