# -*- coding: utf-8 -*-
# Copyright 2015-2018 ACSONE SA/NV
# Copyright 2019 BIG-Cosnulting GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    'name': 'German MIS Builder templates',
    'summary': """
        MIS Builder templates for the German P&L
        and Balance Sheets (SKR04)""",
    'author': 'OpenBIG.org,''ACSONE SA/NV,''Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-germany',
    'category': 'Reporting',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'mis_builder',  # OCA/account-financial-reporting
        'l10n_de_skr04',
    ],
    'data': [
        'data/mis_report_styles.xml',
        'data/mis_report_pl.xml',
        'data/mis_report_bs.xml',
    ],
    'installable': True,
}
