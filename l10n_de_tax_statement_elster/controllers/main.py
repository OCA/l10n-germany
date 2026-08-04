# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import http
from odoo.exceptions import UserError
from odoo.http import content_disposition, request

from ..services.elster_export import (
    generate_elster_xml,
    generate_export_filename,
)

_logger = logging.getLogger(__name__)


class VatStatementElsterController(http.Controller):
    @http.route(
        "/l10n_de_tax_statement_elster/<int:statement_id>/download",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def download_elster_xml(self, statement_id):
        statement = request.env["l10n.de.tax.statement"].browse(statement_id)
        if not statement.exists():
            return request.not_found()

        if statement.state == "draft":
            return request.not_found()

        if statement.version != "2026":
            return request.not_found()

        try:
            xml_bytes = generate_elster_xml(statement)
        except UserError:
            raise
        except Exception:
            _logger.exception("ELSTER XML generation failed")
            return request.not_found()

        filename = generate_export_filename(statement)
        return request.make_response(
            xml_bytes,
            headers=[
                ("Content-Type", "application/xml; charset=iso-8859-15"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )
