# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT(<https://www.nico-solutions.de>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "L10n DIN5008 Report Base",
    "summary": "Base module for DIN 5008 report configs",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "NICO SOLUTIONS - ENGINEERING & IT, Odoo Community Association (OCA)",
    "maintainers": ["NICO-SOLUTIONS"],
    "website": "https://github.com/OCA/l10n-germany",
    "depends": ["web", "l10n_din5008"],
    "data": [
        "report/external_layout_din5008.xml",
        "wizard/base_document_layout_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_din5008_report_base/static/src/components/din5008_config_registry.esm.js",
            "l10n_din5008_report_base/static/src/components/din5008_config_field/*",
            "l10n_din5008_report_base/static/src/components/din5008_config_dialog/*",
        ],
        "web.report_assets_common": [
            "l10n_din5008_report_base/static/src/scss/report_din5008.scss",
        ],
    },
}
