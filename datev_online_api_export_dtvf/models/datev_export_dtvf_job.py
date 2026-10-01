# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DatevExportDtvfExportJob(models.Model):
    _name = "datev_export_dtvf.export.job"
    _description = "DATEV export job"
    _order = "create_date DESC, name"

    export_id = fields.Many2one("datev_export_dtvf.export", required=True)
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    reference = fields.Char()
    location = fields.Char()
    state = fields.Selection(
        [
            ("uploaded", "Uploaded"),
            ("failed", "Failed"),
            ("upload_error", "Upload Error"),
            ("succeeded", "Succeeded"),
        ]
    )
    # URI to the validation details
    detail_type = fields.Char(string="Help")
    # Short human readable description
    detail_title = fields.Char(string="Problem")

    def datev_check_job(self):
        for job in self.filtered("active"):
            data = job.export_id.company_id.datev_upload_dtvf_job(job.location)

            result = (data.get("result") or "").lower()
            if result in {"success", "succeeded"}:
                job.write(
                    {"state": "succeeded", "detail_type": None, "detail_title": None}
                )
            elif result in {"error", "failed", "rejected", "invalid"}:
                validation = data.get("validation_details") or {}
                job.write(
                    {
                        "state": "failed",
                        "detail_type": validation.get("type"),
                        "detail_title": validation.get("title"),
                    }
                )

        for export in self.export_id:
            states = set(export.job_ids.filtered("active").mapped("state"))
            if states == {"succeeded"}:
                export.state = "uploaded"
            elif states & {"failed", "upload_error"}:
                export.state = "failed"
