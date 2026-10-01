# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import re
import zipfile
from datetime import datetime

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DatevExportDtvfExport(models.Model):
    _inherit = "datev_export_dtvf.export"

    state = fields.Selection(
        selection_add=[
            ("processing", "Processing"),
            ("failed", "Failure"),
            ("uploaded", "Uploaded"),
        ]
    )
    datev_api_available = fields.Boolean(related="company_id.datev_api_available")

    job_ids = fields.One2many(
        "datev_export_dtvf.export.job", "export_id", context={"active_test": False}
    )

    def action_upload(self):
        # TODO: It isn't optimal to extract the files again from the ZIP

        for rec in self:
            rec._upload_to_datev()

    def _upload_to_datev(self):
        self.ensure_one()
        if not self.file_data:
            return

        # Archive the existing jobs
        self.job_ids.sudo().active = False

        buffer = io.BytesIO(base64.b64decode(self.file_data))

        uploads, failures = [], []
        jobs = []
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        with zipfile.ZipFile(buffer) as zipf:
            for file in zipf.filelist:
                if not re.match(r"EXTF_.{0,51}\.csv", file.filename):
                    continue

                reference = f"{ts}_{file.filename.replace('.csv', '')}_{self.id}"
                vals = {
                    "export_id": self.id,
                    "name": file.filename,
                    "reference": reference,
                }

                content = zipf.open(file.filename).read()
                if location := self.company_id.datev_upload_dtvf(
                    reference,
                    file.filename,
                    content,
                ):
                    vals.update({"state": None, "location": location})

                    uploads.append(file.filename)
                else:
                    vals["state"] = "upload_error"
                    failures.append(file.filename)

                jobs.append(vals)

        self.job_ids.sudo().create(jobs)

        if failures:
            self.state = "failed"
        elif uploads:
            self.state = "processing"
