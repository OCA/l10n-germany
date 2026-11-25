# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "DIN 5008 Report Layout",
    "summary": "DIN 5008 document layout (Form A / Form B) "
    "based on the Odoo standard report layout",
    "version": "19.0.1.0.0",
    "category": "Reporting",
    "author": "glueckkanja AG, Odoo Community Association (OCA)",
    "maintainers": ["CRogos"],
    "website": "https://github.com/OCA/l10n-germany",
    "license": "AGPL-3",
    "depends": ["web", "l10n_de_report_footer"],
    "data": [
        "views/report_templates.xml",
        "data/report_paperformat.xml",
        "data/report_layout.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "layout_din5008/static/src/scss/layout_din5008.scss",
        ],
    },
}
