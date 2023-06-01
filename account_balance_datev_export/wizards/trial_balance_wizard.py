# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    def button_export_datev_ascii(self):
        data = self._prepare_report_trial_balance()
        ir_report = self.env.ref(
            "account_balance_datev_export.action_report_trial_balance_datev"
        )
        action = ir_report.report_action(self, data=data)
        return action
