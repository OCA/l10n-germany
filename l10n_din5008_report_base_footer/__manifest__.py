# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n DIN5008 Report Base Footer",
    "summary": "Extension module for DIN 5008 report config (footer section)",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "NICO SOLUTIONS - ENGINEERING & IT, Odoo Community Association (OCA)",
    "maintainers": ["NICO-SOLUTIONS"],
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["l10n_din5008_report_base"],
    "data": [
        "report/external_layout_din5008.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_din5008_report_base_footer/static/src/din5008_config_fields.esm.js",
            "l10n_din5008_report_base_footer/static/src/components/din5008_config_dialog/*",
        ],
    },
}
