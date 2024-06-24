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
        if not invoices:
            return

        self.check_valid_data(invoices)

        package_limit = self.env.company.datev_package_limit * 1024 * 1024
        included = invoices.browse()
        file_counter = 0

        buf = io.BytesIO()
        zip_file = zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED)

        for invoice in invoices.with_context(progress_iter=True):
            # create xml file for invoice
            xml_invoice_data = self.generate_xml_invoice(invoice, check_xsd)
            zip_file.writestr(invoice.datev_filename(".xml"), xml_invoice_data[1])
            file_counter += 1

            # attach pdf file for vendor bills
            attachment = self.generate_pdf(invoice)
            if attachment:
                zip_file.writestr(invoice.datev_filename(), attachment)
                file_counter += 1

            included |= invoice

            # The file can grow slightly bigger than the limit
            if buf.tell() > package_limit or file_counter >= 4800:
                # Finalize the file
                zip_file.writestr(*self.generate_xml_document(included, check_xsd))
                zip_file.close()

                yield base64.b64encode(buf.getvalue()), included

                # Open next zip and increment
                file_counter = 0
                buf = io.BytesIO()
                included = invoices.browse()
                zip_file = zipfile.ZipFile(
                    buf, mode="w", compression=zipfile.ZIP_DEFLATED
                )

        # Prozess the las chunk
        if included:
            zip_file.writestr(*self.generate_xml_document(included, check_xsd))
            zip_file.close()

            yield base64.b64encode(buf.getvalue()), included
