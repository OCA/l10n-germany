# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import logging
import zipfile

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DatevZipGenerator(models.AbstractModel):
    _name = "datev.zip.generator"
    _description = "DATEV ZIP Generator"
    _inherit = ["datev.pdf.generator", "datev.xml.generator"]

    @api.model
    def check_valid_data(self, invoices):
        if not invoices:
            raise UserError(_("No Invoices Selected!"))

        for invoice in invoices:
            if not invoice.partner_id.name and not invoice.partner_id.parent_name:
                raise UserError(
                    _(
                        "Data Insufficient!\nYou have to fill the address for "
                        "partner of invoice %s. The partner address has to have "
                        "official company name!"
                    )
                    % invoice.name
                )

    @api.model
    def generate_zip(self, invoices, check_xsd):
        self.check_valid_data(invoices)
        with io.BytesIO() as s, zipfile.ZipFile(s, mode="w") as zip_file:
            xml_document_data = self.generate_xml_document(invoices, check_xsd)
            zip_file.writestr(
                xml_document_data[0],
                xml_document_data[1],
                zipfile.ZIP_DEFLATED,
            )

            for invoice in invoices.with_context(progress_iter=True):
                # create xml file for invoice
                xml_invoice_data = self.generate_xml_invoice(invoice, check_xsd)
                zip_file.writestr(
                    invoice.datev_filename(".xml"),
                    xml_invoice_data[1],
                    zipfile.ZIP_DEFLATED,
                )
                # attach pdf file for vendor bills
                attachment = self.generate_pdf(invoice)
                if attachment:
                    zip_file.writestr(
                        invoice.datev_filename(),
                        attachment,
                        zipfile.ZIP_DEFLATED,
                    )

            zip_file.close()
            return base64.b64encode(s.getvalue())
