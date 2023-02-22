# Copyright 2019 Onestein (<https://www.onestein.eu>)
# Copyright 2019 BIG-Consulting GmbH(<http://www.openbig.org>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'German VAT Statement',
    'version': '12.0.1.0.1',
    'category': 'Localization',
    'license': 'AGPL-3',
    'author': 'OpenBIG.org, Onestein, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-germany',
    'depends': [
        'account_tax_balance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/tax_statement_security_rule.xml',
        'data/paperformat.xml',
        'templates/assets.xml',
        'views/l10n_de_tax_statement_view.xml',
        'views/report_tax_statement.xml',
        'report/report_tax_statement.xml',
        'wizard/l10n_de_tax_statement_config_wizard.xml',
    ],
    'installable': True,
}
