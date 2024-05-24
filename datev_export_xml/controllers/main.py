# Copyright (C) 2022-2024 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import http
from odoo.http import request, send_file

from odoo.addons.web.controllers.main import Home

_logger = logging.getLogger(__name__)


class DatevHome(Home):
    @http.route("/datev/xml/download/<int:line_id>", type="http", auth="user")
    def datev_xml_download_attachment(self, line_id):
        export = request.env["datev.export.xml.line"].search([("id", "=", line_id)])

        if not export.attachment_id:
            return request.not_found()

        att = export.attachment_id

        if att.store_fname:
            full_path = att._full_path(att.store_fname)
            return send_file(
                full_path,
                filename=att.name,
                mimetype=att.mimetype,
                as_attachment=True,
            )

        return request.make_response(
            base64.b64decode(att.datas),
            [
                ("Content-Type", att.mimetype),
                ("Content-Disposition", f'attachment; filename="{att.name}"'),
            ],
        )
