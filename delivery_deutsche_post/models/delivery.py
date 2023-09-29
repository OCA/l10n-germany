from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

import inema
import logging
import requests

KEY_PHASE = "1"
prod_code_with_tracking = ["1022"]


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_account_id = fields.Many2one("carrier.account", "Carrier Account")
    product_code = fields.Char()
    delivery_type = fields.Selection(
        selection_add=[("deutsche_post", "Deutsche Post")],
        ondelete={
            "deutsche_post": lambda recs: recs.write(
                {
                    "delivery_type": "fixed",
                    "fixed_price": 0,
                }
            )
        },
        help="Carrier type (combines several delivery methods)",
    )

    @api.onchange("carrier_account_id")
    def onchange_carrier_account_id(self):
        if self.carrier_account_id:
            self.delivery_type = self.carrier_account_id.delivery_type

    def create_depost_label(self, data, preview=False):
        if not self.carrier_account_id:
            raise UserError(_("No carrier account set"))

        if not self.carrier_account_id.partner_id:
            raise UserError(_("No carrier account partner ID set"))

        if not self.carrier_account_id.partner_key:
            raise UserError(_("No carrier account partner key set"))

        logging.basicConfig(level=logging.INFO)
        im = inema.Internetmarke(self.carrier_account_id.partner_id, self.carrier_account_id.partner_key, KEY_PHASE)

        try:
            im.authenticate(self.carrier_account_id.account, self.carrier_account_id.password)
        except Exception as e:
            raise e from None
        sysmo_addr = im.build_addr(
            street=data["source"]["street2"],
            house="",
            zipcode=data["source"]["zip"],
            city=data["source"]["city"],
            country=data["source"]["country"],
            additional=data["source"]["street"],
        )
        sysmo_naddr = im.build_comp_addr(
            company=data["source"]["name"], address=sysmo_addr
        )

        if data["dest"]["street"] and data["dest"]["street2"]:
            street = data["dest"]["street2"]
            additional = data["dest"]["street"]
        elif data["dest"]["street"]:
            street = data["dest"]["street"]
            additional = ""
        elif data["dest"]["street2"]:
            street = data["dest"]["street2"]
            additional = ""
        else:
            raise UserError(_("Street missing in address"))

        city = ""
        if data["dest"]["state"] and data["dest"]["city"]:
            city = data["dest"]["city"] + ", " + data["dest"]["state"]
        elif data["dest"]["city"]:
            city = data["dest"]["city"]
        elif data["dest"]["state"]:
            city = data["dest"]["state"]

        dest_addr = im.build_addr(
            street=street,
            house="",
            zipcode=data["dest"]["zip"],
            city=city,
            country=data["dest"]["country"],
            additional=additional,
        )

        if not data["dest"]["company"]:
            dest_naddr = im.build_pers_addr(
                first=data["dest"]["first"],
                last=data["dest"]["last"],
                address=dest_addr,
                salutation=None,
                title=data["dest"]["title"],
            )
        else:
            person = im.build_pers_name(
                first=data["dest"]["first"],
                last=data["dest"]["last"],
                salutation=None,
                title=data["dest"]["title"],
            )
            dest_naddr = im.build_comp_addr(
                company=data["dest"]["company"], address=dest_addr, person=person
            )

        position = im.build_position(
            product=data["prod_code"],
            sender=sysmo_naddr,
            receiver=dest_naddr,
            layout="AddressZone",
            pdf=True,
            x=1,
            y=1,
            page=1,
        )
        im.add_position(position)

        if preview:
            resp_data = im.retrievePreviewPDF(
                data["prod_code"], self.carrier_account_id.file_format, layout="AddressZone"
            )
            response = requests.get(resp_data)

            file_name = "Test"
            file_data = response.content

            return False, False, file_name, file_data
        else:
            try:
                resp_data = im.checkoutPDF(self.carrier_account_id.file_format)
            except Exception as e:
                raise UserError(_("Deutsche Post Checkout Error")) from e

            voucher = resp_data["shoppingCart"]["voucherList"]["voucher"][0]
            tracking_id = voucher["trackId"]
            if not tracking_id and data["prod_code"] in prod_code_with_tracking:
                tracking_id = voucher["voucherId"]
            price = im.get_product_price_by_id(data["prod_code"])
            file_name = tracking_id
            if not file_name:
                file_name = voucher["voucherId"]
            file_data = resp_data["pdf_bin"]

            self.env["de.post.logs"].create(
                {
                    "prod_code": data["prod_code"],
                    "format_code": self.carrier_account_id.file_format,
                    "request": "%s\n%s" % (str(sysmo_naddr), str(dest_naddr)),
                    "response": resp_data,
                    "name": data["name"],
                    "account_id": self.carrier_account_id.id,
                    "tracking_num": tracking_id,
                }
            )

            return tracking_id, price, file_name, file_data

    def deutsche_post_send_shipping(self, pickings):
        carrier_acc = False
        product_code = False
        if self.carrier_account_id:
            carrier_acc = self.carrier_account_id
            product_code = self.product_code

        if not carrier_acc or carrier_acc.delivery_type != "deutsche_post":
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

        result = []

        for rec in pickings:
            last_name = (
                rec.partner_id.parent_id.name + ", " + rec.partner_id.name
                if rec.partner_id.parent_id
                and rec.partner_id.name != rec.partner_id.parent_id.name
                else rec.partner_id.name
            )
            last_name = (
                rec.partner_id.parent_id.name + ", " + rec.partner_id.name
                if rec.partner_id.parent_id
                and rec.partner_id.name != rec.partner_id.parent_id.name
                else rec.partner_id.name
            )
            data = {
                "name": rec.name,
                "prod_code": product_code,
                "dest": {
                    "first": "",
                    "last": last_name,
                    "street": rec.partner_id.street or "",
                    "street2": rec.partner_id.street2 or "",
                    "zip": rec.partner_id.zip or "",
                    "city": rec.partner_id.city or "",
                    "country": rec.partner_id.country_id.code_iso or "",
                    "company": "",
                    "title": rec.partner_id.title.shortcut
                    if rec.partner_id.title
                    else "",
                    "state": rec.partner_id.state_id.name or "",
                },
                "source": {
                    "name": rec.company_id.name,
                    "street": rec.company_id.street or "",
                    "street2": rec.company_id.street2 or "",
                    "zip": rec.company_id.zip or "",
                    "city": "%s - %s"
                    % (rec.company_id.city, rec.company_id.country_id.name),
                    "country": rec.company_id.country_id.code_iso or "",
                },
            }
            if not data.get("prod_code"):
                raise UserError(_("Product Code required"))

            if data["prod_code"] not in [k for k in inema.inema.default_products]:
                raise UserError(_("Product Code %s does not exist") % (data["prod_code"]))

            tracking_id, price, file_name, file_data = self.create_depost_label(data)

            vals = {
                "name": f"{rec.name}_{file_name or ''}",
                "raw": file_data,
                "mimetype": "application/pdf",
                "res_model": "stock.picking",
                "res_id": rec.id,
            }

            label_attachment = self.env["ir.attachment"].create(vals)

            rec.label_de_attach_id = label_attachment.id

            result.append({"exact_price": price, "tracking_number": tracking_id})

        return result

    def deutsche_post_rate_shipment(self, order):
        raise ValidationError(
            _("Deutsche Post: Rating shipping is not supported.")
        )

    def deutsche_post_get_tracking_link(self, picking):
        raise ValidationError(
            _("Deutsche Post: Tracking link generation is not supported.")
        )

    def deutsche_post_cancel_shipment(self, pickings):
        raise ValidationError(
            _("Deutsche Post: Cancellation of shipment is not supported.")
        )
