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

    @api.model
    def _csv_float_conversion(self, value):
        return "{:.2f}".format(float_round(value, 2)).replace(".", ",")

    def generate_csv_report(self, writer, data, recs):
        report = self.env["report.account_financial_report.trial_balance"]
        data = report._get_report_values(recs.ids, data)

        writer.writeheader()
        fields = self._csv_field_mapping()
        for balance in data.get("trial_balance", []):
            if balance["type"] == "account_type":
                ending = balance["ending_balance"]
                writer.writerow(
                    {
                        fields["code"]: balance["code"],
                        fields["name"]: balance["name"],
                        fields["debit"]: self._csv_float_conversion(balance["debit"]),
                        fields["credit"]: self._csv_float_conversion(balance["credit"]),
                        fields["ending_debit"]: self._csv_float_conversion(
                            max(0, ending)
                        ),
                        fields["ending_credit"]: self._csv_float_conversion(
                            max(0, -ending)
                        ),
                    }
                )

    def csv_report_options(self):
        res = super().csv_report_options()
        res["delimiter"] = ";"
        res["fieldnames"].extend(self._csv_field_mapping().values())
        res["quoting"] = csv.QUOTE_NONE
        return res
