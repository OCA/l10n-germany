import base64
import html
import logging
import os
import re
import time
from tempfile import NamedTemporaryFile

import inema  # pip3 install git+https://gitlab.com/gsauthof/python-inema.git
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from . import pypdftk

# please set the path as per pdftk installed on OS
# pypdftk.PDFTK_PATH = '/usr/local/bin/pdftk'

KEY_PHASE = "1"
prod_code_with_tracking = ["1022"]


def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError as e:
                logging.exception(e)
        else:
            # named entity
            try:
                text = chr(html.entities.name2codepoint[text[1:-1]])
            except KeyError as e:
                logging.exception(e)
        return text  # leave as is

    return re.sub(r"&#?\w+;", fixup, text)


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    partner_id = fields.Char("Partner ID")
    partner_key = fields.Char()
    file_format = fields.Selection(
        selection="_selection_file_format",
        help="Default format of the carrier's label you want to print",
        required=True,
        default="26",
    )
    delivery_type = fields.Selection(
        selection="_get_carrier_delivery_type",
        required=True,
        help="In case of several carriers, help to know which account "
        "belong to which carrier",
    )

    @api.model
    def _selection_file_format(self):
        resp = super()._selection_file_format()
        for fmt in inema.inema.formats:
            resp.append((str(fmt["id"]), "[%s] %s" % (fmt["id"], fmt["name"])))
        return resp

    def _get_carrier_delivery_type(self):
        resp = []
        resp.append(("deutsche_post", "Deutsche Post"))
        return resp

    def test_connection(self):
        return {
            "type": "ir.actions.act_window",
            "name": "File",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "download.file",
            "target": "new",
        }

    def view_logs(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "de.post.logs",
            "view_type": "form",
            "view_mode": "tree,form",
            "target": "current",
        }

    def view_forms(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "carrier.form",
            "view_type": "form",
            "view_mode": "tree,form",
            "target": "current",
        }


class DownloadFile(models.TransientModel):
    _name = "download.file"
    _description = "Download File"

    file = fields.Binary(readonly="1")
    file_name = fields.Char()
    prod_code = fields.Char(default=147)
    picking_id = fields.Many2one("stock.picking", "Test Picking")

    def test_connection(self):
        test_data = {
            "name": "Test/Preview",
            "prod_code": self.prod_code,
            "dest": {
                "first": "",
                "last": "Herald Welte",
                "street": "Glanzstrasse 11",
                "street2": "",
                "zip": "12437",
                "city": "Berlin",
                "state": "",
                "country": "",
                "title": "Mr.",
                "company": "Orange GmbH",
            },
            "source": {
                "name": self.env.user.company_id.name,
                "street": self.env.user.company_id.street or "",
                "street2": self.env.user.company_id.street2 or "",
                "zip": self.env.user.company_id.zip or "",
                "city": "%s - %s"
                % (
                    self.env.user.company_id.city,
                    self.env.user.company_id.country_id.name,
                ),
                "country": self.env.user.company_id.country_id.code_iso or "",
            },
        }
        _, _, file_name, file_data = self.picking_id.carrier_id.create_depost_label(test_data, preview=True)

        carrier_form = self.env["carrier.form"].search(
            [("prod_code", "=", self.prod_code)]
        )
        if carrier_form:
            file_data = carrier_form.append_carrier_form(file_data, self.picking_id)

        self.write(
            {"file": base64.b64encode(file_data), "file_name": (file_name or "_Download_") + ".pdf"}
        )

        return {
            "type": "ir.actions.act_window",
            "name": "File",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "download.file",
            "target": "new",
            "res_id": self.id,
        }


class DeutschePostLogs(models.Model):
    _name = "de.post.logs"
    _description = "Deutsche Post Logs"
    _order = "create_date desc"

    prod_code = fields.Char("Product Code")
    format_code = fields.Char()
    account_id = fields.Many2one("carrier.account", "Carrier Account")
    tracking_num = fields.Char("Tracking ID")
    name = fields.Char()
    request = fields.Text()
    response = fields.Text("Response/URL")


class CarrierForm(models.Model):
    _name = "carrier.form"
    _description = "Deutsche Carrier Form"

    prod_code = fields.Char("Deutsche Label Product Code")
    pdf_file_id = fields.Many2one("ir.attachment", "Form PDF")
    field_ids = fields.One2many("carrier.form.field", "form_id", string="Variables")

    def append_carrier_form(self, label_pdf, picking=False):
        label_file = NamedTemporaryFile(delete=False)
        source_file = NamedTemporaryFile(delete=False)
        flatten_file = NamedTemporaryFile(delete=False)
        merged_file = NamedTemporaryFile(delete=False)

        with open(label_file.name, "wb") as f:
            f.write(base64.b64decode(label_pdf))  # label_pdf.decode('base64')
            label_file.close()

        with open(source_file.name, "wb") as f:
            f.write(
                base64.b64decode(self.pdf_file_id.datas)
            )  # self.pdf_file_id.datas.decode('base64')
            source_file.close()

        datas = {}
        eval_context = {
            "picking": picking,
            "self": self,
            "user": self.env.user,
            "time": time,
        }
        for var in self.field_ids:
            safe_eval(var.code.strip(), eval_context, mode="exec", nocopy=True)
            if "result" in eval_context:
                datas[var.name] = eval_context["result"]

        pypdftk.fill_form(
            source_file.name, datas=datas, out_file=flatten_file.name, flatten=True
        )

        pypdftk.concat([label_file.name, flatten_file.name], out_file=merged_file.name)

        fp = open(merged_file.name, "rb")
        merged_file_data = fp.read()
        fp.close()

        os.unlink(label_file.name)
        os.unlink(source_file.name)
        os.unlink(flatten_file.name)
        os.unlink(merged_file.name)

        return base64.encodestring(merged_file_data)

    def find_fields(self):
        self.ensure_one()

        source_file = NamedTemporaryFile(delete=False)
        with open(source_file.name, "wb") as f:
            f.write(self.pdf_file_id.datas.decode("base64"))
            source_file.close()

        resp = pypdftk.run_command(
            [pypdftk.PDFTK_PATH, source_file.name, "dump_data_fields"]
        )

        for fld in resp:
            fld_parts = fld.split(":")
            if fld_parts[0] == "FieldName":
                fld_name = unescape(fld_parts[1].strip())
                if not self.env["carrier.form.field"].search(
                    [("name", "=", fld_name), ("form_id", "=", self.id)]
                ):
                    self.env["carrier.form.field"].create(
                        {"name": fld_name, "form_id": self.id}
                    )

        os.unlink(source_file.name)


class CarrierFormField(models.Model):
    _name = "carrier.form.field"
    _description = "Deutsche Post Form Field"

    form_id = fields.Many2one("carrier.form", "From", required=1)
    name = fields.Char("Form Variable Name", required=1)
    code = fields.Text(required=1, default='result=""')
