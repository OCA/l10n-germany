# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import csv

from odoo import api, models
from odoo.tools import float_round


class PartnerCSV(models.AbstractModel):
    _name = "report.account_balance_datev_export.account_balance_datev"
    _inherit = "report.report_csv.abstract"
    _description = "DATEV ASCII Trial Balance"

    @api.model
    def _csv_field_mapping(self):
        return {
            "code": "Konto",
            "name": "Kontobezeichnung",
            "debit": "EB-Wert Soll",
            "credit": "EB-Wert Haben",
            "ending_debit": "VZ Soll",
            "ending_credit": "VZ Haben",
        }

    def generate_csv_report(self, writer, data, recs):
        report = self.env["report.account_financial_report.trial_balance"]
        data = report._get_report_values(recs.ids, data)

        writer.writeheader()
        fields = self._csv_field_mapping()
        for balance in data.get("trial_balance", []):
            if balance["type"] == "account_type":
                ending = float_round(balance["ending_balance"], 2)
                writer.writerow(
                    {
                        fields["code"]: balance["code"],
                        fields["name"]: balance["name"],
                        fields["debit"]: float_round(balance["debit"], 2),
                        fields["credit"]: float_round(balance["credit"], 2),
                        fields["ending_debit"]: ending if ending > 0 else 0,
                        fields["ending_credit"]: -ending if ending < 0 else 0,
                    }
                )

    def csv_report_options(self):
        res = super().csv_report_options()
        res["delimiter"] = ";"
        res["fieldnames"].extend(self._csv_field_mapping().values())
        res["quoting"] = csv.QUOTE_NONE
        return res
