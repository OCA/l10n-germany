# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class VatStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    zm_line_ids = fields.One2many(
        "l10n.de.tax.statement.zm.line",
        "statement_id",
        string="ZM Lines",
        readonly=True,
    )
    zm_total = fields.Monetary(
        string="Total ZM amount",
        readonly=True,
        help="Total amount in currency of the statement.",
    )

    def _compute_zm_lines(self):
        """Computes ZM lines for the report"""
        zmline = self.env["l10n.de.tax.statement.zm.line"]
        for statement in self:
            statement.zm_line_ids.unlink()
            statement.zm_total = 0.0
            amounts_map = statement._get_partner_amounts_map()
            for partner_id in amounts_map:
                zm_values = self._prepare_zm_line(amounts_map[partner_id])
                zm_values["partner_id"] = partner_id
                zm_values["statement_id"] = statement.id
                newline = zmline.create(zm_values)
                statement.zm_line_ids += newline
                zm_total = newline.amount_products + newline.amount_services
                statement.zm_total += zm_total

    @api.model
    def _prepare_zm_line(self, partner_amounts):
        """Prepares an internal data structure representing the ZM line"""
        return {
            "country_code": partner_amounts["country_code"],
            "vat": partner_amounts["vat"],
            "amount_products": partner_amounts["amount_products"],
            "amount_services": partner_amounts["amount_services"],
            "currency_id": partner_amounts["currency_id"],
        }

    def _check_line_code(self, line, line_code):
        tags_map = self._get_tags_map()
        for tag in line.tax_tag_ids:
            tag_map = tags_map.get(tag.id)
            if tag_map:
                code, column = tag_map
                code = self._strip_sign_in_tag_code(code)
                if code == line_code:
                    return True

            return False

    def _is_41_line(self, line):
        return self._check_line_code(line, "41")

    def _is_21_line(self, line):
        return self._check_line_code(line, "21")

    def _get_partner_amounts_map(self):
        """Generate an internal data structure representing the ICP line"""
        self.ensure_one()

        partner_amounts_map = {}
        for line in self.move_line_ids:
            is_41 = self._is_41_line(line)
            is_21 = self._is_21_line(line)
            if is_41 or is_21:
                vals = self._prepare_zm_line_from_move_line(line)
                if vals["partner_id"] not in partner_amounts_map:
                    self._init_partner_amounts_map(partner_amounts_map, vals)
                self._update_partner_amounts_map(partner_amounts_map, vals)
        return partner_amounts_map

    @classmethod
    def _update_partner_amounts_map(cls, partner_amounts_map, vals):
        """Update amounts of the internal ICP lines data structure"""
        map_data = partner_amounts_map[vals["partner_id"]]
        map_data["amount_products"] += vals["amount_products"]
        map_data["amount_services"] += vals["amount_services"]

    @classmethod
    def _init_partner_amounts_map(cls, partner_amounts_map, vals):
        """Initialize the internal ICP lines data structure"""
        partner_amounts_map[vals["partner_id"]] = {
            "country_code": vals["country_code"],
            "vat": vals["vat"],
            "currency_id": vals["currency_id"],
            "amount_products": 0.0,
            "amount_services": 0.0,
        }

    def _prepare_zm_line_from_move_line(self, line):
        """Gets move line details and prepares ZM report line data"""
        self.ensure_one()

        balance = line.balance
        if line.company_currency_id != self.currency_id:
            balance = line.company_currency_id.with_context(date=line.date).compute(
                balance, self.currency_id, round=True
            )
        amount_products = balance * -1
        amount_services = 0.0
        if self._is_21_line(line):
            amount_products = 0.0
            amount_services = balance * -1

        return {
            "partner_id": line.move_id.partner_shipping_id.id,
            "country_code": line.move_id.partner_shipping_id.country_id.code,
            "vat": line.move_id.partner_shipping_id.vat,
            "amount_products": amount_products,
            "amount_services": amount_services,
            "currency_id": self.currency_id.id,
        }

    def reset(self):
        """Removes ZM lines if reset to draft"""
        for statement in self:
            statement.zm_line_ids.unlink()
        return super(VatStatement, self).reset()

    def post(self):
        """Checks configuration when validating the statement"""
        self.ensure_one()
        res = super(VatStatement, self).post()
        self._compute_zm_lines()
        return res

    @api.model
    def _modifiable_values_when_posted(self):
        """Returns the modifiable fields even when the statement is posted"""
        res = super(VatStatement, self)._modifiable_values_when_posted()
        res.append("zm_line_ids")
        res.append("zm_total")
        return res

    def zm_update(self):
        """Update button"""
        self.ensure_one()

        if self.state in ["final"]:
            raise UserError(_("You cannot modify a final statement!"))

        # clean old lines
        self.zm_line_ids.unlink()

        # create lines
        self._compute_zm_lines()

    def _round_zm_amount(self, x, n=0):
        try:
            return int(x / abs(x) * int(abs(x) * 10**n + 0.5) / 10**n)
        except ZeroDivisionError:
            return 0

    def _generate_zm_download_lines(self):
        self.ensure_one()
        res = {}
        for zml in self.zm_line_ids:
            if not zml.vat:
                raise UserError(
                    _("Partner {} has no vat id!").format(zml.partner_id.name)
                )
            vat = zml.vat.replace(" ", "").replace("-", "")
            if vat not in res:
                res[vat] = {
                    "1_country": vat[:2],
                    "2_vat": vat[2:],
                    "3_amount_products": zml.amount_products,
                    "4_amount_services": zml.amount_services,
                }
            else:
                res[vat]["3_amount_products"] += zml.amount_products
                res[vat]["4_amount_services"] += zml.amount_services
        lines = [
            ["Laenderkennzeichen", "USt-IdNr.", "Betrag(Euro)", "Art der Leistung"]
        ]
        for vat in res:
            v = res[vat]
            amount_products = self._round_zm_amount(v["3_amount_products"])
            if amount_products:
                lines.append([v["1_country"], v["2_vat"], amount_products, "L"])
            amount_services = self._round_zm_amount(v["4_amount_services"])
            if amount_services:
                lines.append([v["1_country"], v["2_vat"], amount_services, "S"])
        return lines

    def zm_download(self):
        """Download button"""
        self.ensure_one()
        self._generate_zm_download_lines()
        zm_download = "\n".join(
            ",".join(str(i) for i in line)
            for line in self._generate_zm_download_lines()
        )
        zm_download_base64 = base64.b64encode(zm_download.encode("iso-8859-15"))
        attachment_id = self.env["ir.attachment"].create(
            {
                "name": "{}.csv".format(self.name),
                "datas": zm_download_base64,
                "public": True,
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/{}?download=true".format(attachment_id.id),
            "target": "new",
            "nodestroy": False,
        }
