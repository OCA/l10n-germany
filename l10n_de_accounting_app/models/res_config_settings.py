# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

_MODULE_FIELDS = [
    "module_account_edi_ubl_cii",
    "module_account_invoice_overdue_reminder",
    "module_account_credit_control",
    "module_l10n_de_mis_reports",
    "module_account_statement_import_sheet_file",
    "module_account_statement_import_camt54",
    "module_account_statement_import_online_paypal",
    "module_account_statement_import_online_ponto",
    "module_account_statement_import_online_stripe",
    "module_datev_export_dtvf",
    "module_datev_export_xml",
    "module_datev_import_csv_dtvf",
    "module_l10n_de_tax_statement",
    "module_l10n_de_tax_statement_zm",
    "module_hr_expense_meal_allowance",
    "module_account_payment_mode",
    "module_account_payment_order",
    "module_account_banking_sepa_credit_transfer",
    "module_account_banking_sepa_direct_debit",
    "module_l10n_din5008_move_name",
    "module_account_move_name_sequence",
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Invoice Import/Export EDI
    module_account_edi_ubl_cii = fields.Boolean(
        string="UBL/CII e-invoicing",
    )

    # Followup (Mahnwesen)
    module_account_invoice_overdue_reminder = fields.Boolean(
        string="Overdue Invoice Reminders",
    )
    module_account_credit_control = fields.Boolean(
        string="Credit Control (Mahngebühren)",
    )

    # Reporting
    module_l10n_de_mis_reports = fields.Boolean(
        string="German MIS Reports (P&L, Balance Sheet, SKR03/04)",
    )

    # Bank Import
    module_account_statement_import_sheet_file = fields.Boolean(
        string="CSV/Excel Bank Statement Import",
    )
    module_account_statement_import_camt54 = fields.Boolean(
        string="CAMT.054 Bank Statement Import",
    )
    module_account_statement_import_online_paypal = fields.Boolean(
        string="PayPal Online Statement Import",
    )
    module_account_statement_import_online_ponto = fields.Boolean(
        string="Ponto Online Statement Import",
    )
    module_account_statement_import_online_stripe = fields.Boolean(
        string="Stripe Online Statement Import",
    )

    # DATEV
    module_datev_export_dtvf = fields.Boolean(
        string="DATEV DTVF Export",
    )
    module_datev_export_xml = fields.Boolean(
        string="DATEV XML Export (with PDF)",
    )
    module_datev_import_csv_dtvf = fields.Boolean(
        string="DATEV CSV/DTVF Import",
    )

    # VAT Report (USt-VA) + ZM
    module_l10n_de_tax_statement = fields.Boolean(
        string="German VAT Statement (USt-VA)",
    )
    module_l10n_de_tax_statement_zm = fields.Boolean(
        string="Zusammenfassende Meldung (ZM)",
    )

    # Expense accounting (travel/meal)
    module_hr_expense_meal_allowance = fields.Boolean(
        string="Meal Allowance Expenses",
    )

    # Payment
    module_account_payment_mode = fields.Boolean(
        string="Payment Modes",
    )
    module_account_payment_order = fields.Boolean(
        string="Payment Orders",
    )
    module_account_banking_sepa_credit_transfer = fields.Boolean(
        string="SEPA Credit Transfer",
    )
    module_account_banking_sepa_direct_debit = fields.Boolean(
        string="SEPA Direct Debit",
    )

    # PDF Report
    module_l10n_din5008_move_name = fields.Boolean(
        string="DIN 5008 Move Name in PDF",
    )

    # Nice to Have
    module_account_move_name_sequence = fields.Boolean(
        string="Custom Sequences per Journal",
    )

    @api.onchange(*_MODULE_FIELDS)
    def _onchange_check_module_available(self):
        """Warn and untick a selected module that is not in the addons path."""
        modules = self.env["ir.module.module"].sudo()
        missing = []
        for field_name in _MODULE_FIELDS:
            if not self[field_name]:
                continue
            module_name = field_name[len("module_") :]
            if not modules.search_count([("name", "=", module_name)]):
                missing.append(module_name)
                self[field_name] = False
        if not missing:
            return None
        message = _(
            "These modules are not available and cannot be installed:\n\n"
            "%(names)s\n\n"
            "Add the matching OCA repository to your addons path and update "
            "the apps list (Apps → Update Apps List), then try again.",
            names="\n".join(f"- {name}" for name in missing),
        )
        return {"warning": {"title": _("Module Not Available"), "message": message}}
