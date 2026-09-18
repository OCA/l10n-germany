# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n DIN5008 Report Company Sender Address",
    "summary": "Adds a configurable company sender address to "
    "the DIN 5008 external layout.",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "NICO SOLUTIONS - ENGINEERING & IT, Odoo Community Association (OCA)",
    "maintainers": ["NICO-SOLUTIONS"],
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["l10n_din5008"],
    "data": [
        "report/external_layout_din5008.xml",
        "wizard/base_document_layout_views.xml",
    ],
}
