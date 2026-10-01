# © 2026 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _datev_api_scope(self):
        return super()._datev_api_scope() | {"datev:accounting:extf-files-import"}

    def _datev_dtvf_base_url(self):
        return {
            "live": "https://accounting-extf-files.api.datev.de/platform/v3",
            "test": "https://accounting-extf-files.api.datev.de/platform-sandbox/v3",
        }.get(self.datev_api)

    def datev_upload_dtvf_job(self, location):
        self.ensure_one()
        self._datev_ensure_api_token()
        base_url = self._datev_dtvf_base_url()

        if not base_url:
            return None

        response = requests.get(
            url=f"{base_url}/{location}",
            headers={
                "Accept": "application/json;charset=utf-8",
                "Authorization": f"Bearer {self.datev_api_token}",
                "X-DATEV-Client-Id": self.datev_api_client_id,
            },
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()

        return None

    def datev_upload_dtvf(self, reference_id, filename, data):
        self.ensure_one()
        self._datev_ensure_api_token()
        base_url = self._datev_dtvf_base_url()

        if not base_url:
            raise UserError(self.env._("The DATEV API is currently disabled"))

        client_id = f"{self.datev_consultant_number}-{self.datev_client_number}"

        response = requests.post(
            url=f"{base_url}/clients/{client_id}/extf-files/import",
            headers={
                "Accept": "application/json;charset=utf-8",
                "Authorization": f"Bearer {self.datev_api_token}",
                "X-DATEV-Client-Id": self.datev_api_client_id,
                "Reference-Id": reference_id,
                "Filename": filename,
            },
            data=data,
            timeout=5,
        )

        if 200 <= response.status_code < 300:
            return response.headers.get("Location")

        if response.headers.get("Content-Type") == "application/problem+json":
            _logger.debug(response.text)

        return None

    def _cron_datev_tasks(self):
        res = super()._cron_datev_tasks()

        # Automatically upload files
        self.env["datev_export_dtvf.export"].search(
            [("state", "=", "done")]
        ).action_upload()

        # Fetch the state as long as there is no state set
        self.env["datev_export_dtvf.export.job"].search(
            [("state", "=", False), ("active", "=", True)]
        ).datev_check_job()

        return res
