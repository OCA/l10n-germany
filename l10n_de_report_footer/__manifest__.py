# Copyright 2026 glueckkanja AG
# Copyright 2026 NICO SOLUTIONS - ENGINEERING & IT
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Report Footer (Germany)",
    "summary": "Company footer configuration shared by report layouts: "
    "placeholders, footer lines, bottom margin",
    "version": "19.0.1.0.0",
    "category": "Reporting",
    "author": "glueckkanja AG, NICO SOLUTIONS - ENGINEERING & IT, "
    "Odoo Community Association (OCA)",
    "maintainers": ["CRogos"],
    "website": "https://github.com/OCA/l10n-germany",
    "license": "AGPL-3",
    "depends": ["mail", "web"],
    "data": [
        "views/report_templates.xml",
        "wizard/base_document_layout_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_de_report_footer/static/src/js/report_preview_highlight.esm.js",
            "l10n_de_report_footer/static/src/js/report_layout_config_field.esm.js",
            "l10n_de_report_footer/static/src/xml/report_layout_config_field.xml",
        ],
        "web.report_assets_common": [
            "l10n_de_report_footer/static/src/scss/report_preview_highlight.scss",
        ],
    },
}
