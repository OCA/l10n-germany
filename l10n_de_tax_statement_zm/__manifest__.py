# Copyright 2020 sewisoft (<https://sewisoft.de>)
# Copyright 2019 BIG-Consulting GmbH (<http://www.openbig.org>)
# Copyright 2019 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'German VAT Statement Extension',
    'version': '12.0.1.0.0',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'OpenBIG.org, Onestein, sewisoft, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-germany',
    'depends': [
        'l10n_de_tax_statement',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_de_vat_statement_view.xml',
        'views/report_tax_statement.xml',
        'report/report_tax_statement.xml',
    ],
    'installable': True,
}
