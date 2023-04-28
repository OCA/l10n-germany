from odoo import _, fields, models
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"

    label_de_attach_id = fields.Many2one(
        "ir.attachment", "Label Deutsche Post", copy=False
    )

    def get_deutsche_post_label(self):
        self.ensure_one()

        if self.label_de_attach_id:
            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/?model=ir.attachment&id="
                + str(self.label_de_attach_id.id)
                + "&field=datas&download=true&filename_field=name",
                "target": "download",
            }

        carrier_acc = False
        product_code = False
        if self.carrier_id.carrier_account_id:
            carrier_acc = self.carrier_id.carrier_account_id
            product_code = self.carrier_id.product_code

        if not carrier_acc or carrier_acc.type != "deutsche_post":
            raise UserError(
                _(
                    "There is not any Deutsche post account associated with the delivery method"
                )
            )

        if not product_code:
            raise UserError(
                _(
                    "Please configure Product Code along with Carrier account in Carrier or Grid configuration"  # noqa: B950
                )
            )

        partner = self.partner_id
        parent_name = partner.parent_id.name or ""
        company_name = partner.company_name or ""
        last_name = (
            f"{parent_name}, {partner.name}"
            if parent_name and parent_name != partner.name
            else f"{company_name}, " f"{partner.name}"
            if company_name and company_name != partner.name
            else partner.name
        )

        data = {
            "name": self.name,
            "prod_code": product_code,
            "dest": {
                "first": "",
                "last": last_name,
                "street": self.partner_id.street or "",
                "street2": self.partner_id.street2 or "",
                "zip": self.partner_id.zip or "",
                "city": self.partner_id.city or "",
                "country": self.partner_id.country_id.code_iso or "",
                "company": "",
                #                and self.partner_id.name != self.partner_id.parent_id.name
                #                and self.partner_id.parent_id.name
                #                or self.partner_id.company_name
                #                and self.partner_id.name != self.partner_id.company_name
                #                and self.partner_id.company_name
                #                or "",
                "title": self.partner_id.title.shortcut
                if self.partner_id.title
                else "",
                "state": self.partner_id.state_id.name or "",
            },
            "source": {
                "name": self.company_id.name,
                "street": self.company_id.street or "",
                "street2": self.company_id.street2 or "",
                "zip": self.company_id.zip or "",
                "city": "%s - %s"
                % (self.company_id.city, self.company_id.country_id.name),
                "country": self.company_id.country_id.code_iso or "",
            },
        }

        tracking_number, label_pdf = carrier_acc.get_label(data)
        file_name = "DE_POST_" + (tracking_number or "") + ".pdf"

        carrier_form = self.env["carrier.form"].search(
            [("prod_code", "=", data["prod_code"])]
        )
        if carrier_form:
            label_pdf = carrier_form.append_carrier_form(label_pdf, picking=self)

        attach = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": label_pdf,
                "res_id": self.id,
                "res_model": "stock.picking",
                "type": "binary",
            }
        )

        picking_vals = {"label_de_attach_id": attach.id}

        if tracking_number:
            picking_vals.update(
                {"carrier_tracking_ref": tracking_number.replace(" ", "")}
            )
        self.write(picking_vals)

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/?model=ir.attachment&id="
            + str(self.label_de_attach_id.id)
            + "&field=datas&filename_field=name&download=true",
            "target": "download",
        }

    def _action_done(self):
        res = super()._action_done()
        for pick in self:
            if (
                pick.picking_type_id.code == "outgoing"
                and pick.carrier_id.delivery_type == "deutsche_post"
            ):
                pick.get_deutsche_post_label()
        return res
