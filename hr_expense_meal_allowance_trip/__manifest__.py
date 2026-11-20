# Copyright 2026 glueckkanja AG
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

{
    "name": "HR Expense Meal Allowance Trip",
    "author": "glueckkanja AG, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-germany",
    "category": "Human Resources/Expenses",
    "license": "AGPL-3",
    "summary": "Create German meal allowances directly from a trip",
    "version": "19.0.1.0.0",
    "depends": ["hr_expense_meal_allowance", "hr_expense_trip"],
    "maintainers": ["CRogos"],
    "data": [
        "views/hr_trip_views.xml",
    ],
    "installable": True,
    "auto_install": True,
    "application": False,
}
