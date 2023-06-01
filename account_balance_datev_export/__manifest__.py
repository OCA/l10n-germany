# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Balance DATEV ASCII Export",
    "version": "14.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "license": "AGPL-3",
    "depends": [
        "account_financial_report",
        "report_csv",
    ],
    "data": [
        "report.xml",
        "wizards/trial_balance_wizard_views.xml",
    ],
    "installable": True,
}
