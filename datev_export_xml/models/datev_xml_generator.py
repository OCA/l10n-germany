# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

from lxml import etree

from odoo import _, api, models, tools
from odoo.exceptions import UserError


class DatevXmlGenerator(models.AbstractModel):
    _name = "datev.xml.generator"
    _description = "DATEV XML Generator"

    @api.model
    def check_xml_file(self, doc_name, root, xsd=None):
        if not xsd:
            xsd = "Document_v050.xsd"

        schema = tools.file_open(f"datev_export_xml/xsd_files/{xsd}")
        try:
            schema = etree.XMLSchema(etree.parse(schema))
            schema.assertValid(root)
        except (etree.DocumentInvalid, etree.XMLSyntaxError) as e:
            raise UserError(
                _(
                    "Wrong Data in XML file!\nTry to solve the problem with "
                    "'%s' according to message below:\n\n"
                )
                % doc_name
                + tools.ustr(e)
            ) from e
        return True

    @api.model
    def generate_xml_document(self, invoices, check_xsd=True):
        template = self.env.ref("datev_export_xml.export_invoice_document")
        root = etree.fromstring(
            template.render({"docs": invoices, "company": self.env.company}),
            parser=etree.XMLParser(remove_blank_text=True),
        )

        if check_xsd:
            self.check_xml_file(
                "document.xml", root, "Document_v050.xsd",
            )

        return "document.xml", etree.tostring(root)

    @api.model
    def generate_xml_invoice(self, invoice, check_xsd=True):
        doc_name = re.sub(r"[^a-zA-Z0-9_\-.()]", "", f"{invoice.name}.xml")
        template = self.env.ref("datev_export_xml.export_invoice")
        root = etree.fromstring(
            template.render({"doc": invoice}),
            parser=etree.XMLParser(remove_blank_text=True),
        )

        if check_xsd:
            self.check_xml_file(
                doc_name, root, "Belegverwaltung_online_invoice_v050.xsd",
            )

        return doc_name, etree.tostring(root)
