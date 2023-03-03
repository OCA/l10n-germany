# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class DatevPdfGenerator(models.AbstractModel):
    _name = "datev.pdf.generator"
    _description = "DATEV PDF Generator"

    @api.model
    def report_name(self):
        return "account.report_invoice"

    @api.model
    def find_existing_attachments(self, invoice):
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_field", "=", False),
                ("res_id", "=", invoice.id),
                ("mimetype", "=", "application/pdf"),
                ("file_size", ">", 0),
            ],
            order="create_date DESC",
            limit=1,
        )

    @api.model
    def generate_pdf(self, invoice):
        # Look for the last attached PDF file assuming this is the most recent
        # and valid one
        attachment = self.find_existing_attachments(invoice)

        if attachment:
            return base64.b64decode(attachment["datas"])

        # Otherwise generate a new once
        report = self.env["ir.actions.report"].search(
            [
                ("model", "=", "account.move"),
                ("report_name", "=", self.report_name()),
            ],
        )
        if report:
            return report._render(invoice.ids)[0]
