# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "German VAT Statement ZM ERiC",
    "summary": "Send the Zusammenfassende Meldung to the BZSt with ERiC",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "development_status": "Alpha",
    "depends": ["l10n_de_tax_statement_zm", "l10n_de_tax_statement_eric"],
    "data": ["views/l10n_de_tax_statement_view.xml"],
    "auto_install": True,
    "maintainers": ["mt-software-de"],
}
