# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "DATEV Online API - Export DTVF",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "summary": "Allows the upload of the DTVF directly to datev",
    "depends": [
        "datev_online_api",
        "datev_export_dtvf",
    ],
    "data": [
        "views/datev_export_dtvf_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
