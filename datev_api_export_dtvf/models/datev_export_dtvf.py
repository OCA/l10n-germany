# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import re
import zipfile

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DatevExportDtvfExport(models.Model):
    _inherit = "datev_export_dtvf.export"

    state = fields.Selection(selection_add=[("uploaded", "Uploaded")])
    datev_api_available = fields.Boolean(related="company_id.datev_api_available")

    def action_upload(self):
        # TODO: It isn't optimal to extract the files again from the ZIP

        for rec in self:
            rec._upload_to_datev()

    def _upload_to_datev(self):
        self.ensure_one()
        if not self.file_data:
            return

        buffer = io.BytesIO(base64.b64decode(self.file_data))

        uploads, failures = [], []
        with zipfile.ZipFile(buffer) as zipf:
            for file in zipf.filelist:
                if not re.match(r"EXTF_.{0,51}\.csv", file.filename):
                    continue

                content = zipf.open(file.filename).read()
                if self.company_id.datev_upload_dtvf(
                    file.filename.replace(".csv", "") + str(self.id),
                    file.filename,
                    content,
                ):
                    uploads.append(file.filename)
                else:
                    failures.append(file.filename)

        if failures:
            _logger.warning(f"Failed to upload {self}: {', '.join(failures)}")
        elif uploads:
            self.state = "uploaded"
