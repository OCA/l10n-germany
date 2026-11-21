# Copyright 2015-2018 ACSONE SA/NV
# Copyright 2019 BIG-Cosnulting GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "German MIS Builder templates",
    "summary": """
        MIS Builder templates for the German P&L
        and Balance Sheets (SKR03 + SKR04)""",
    "author": "OpenBIG.org,ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "category": "Reporting",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "mis_builder",  # OCA/mis-builder
        "l10n_de",
    ],
    "data": [
        "data/mis_report_styles.xml",
        "data/mis_report_pl_skr03.xml",
        "data/mis_report_pl_skr04.xml",
        "data/mis_report_bs_skr03.xml",
        "data/mis_report_bs_skr04.xml",
    ],
    "installable": True,
}
