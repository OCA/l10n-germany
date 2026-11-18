# Copyright 2018 Onestein (<http://www.onestein.eu>)
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields, models
from odoo.exceptions import UserError

# The Kennzahlen of the tax statement the ZM is made of
ZM_TAGS = {"41": "amount_products", "21": "amount_services"}


class L10nDeTaxStatement(models.Model):
    _inherit = "l10n.de.tax.statement"

    zm_line_ids = fields.One2many(
        "l10n.de.tax.statement.zm.line",
        "statement_id",
        string="ZM Lines",
        readonly=True,
        copy=False,
    )

    def _get_zm_amounts(self):
        """Return the amounts of products and services by partner, signed like
        the amounts of the tax statement"""
        self.ensure_one()
        amounts = {}
        for tag_name, amount_field in ZM_TAGS.items():
            tags = self.env["account.account.tag"]._get_tax_tags(
                tag_name, self.env.ref("base.de").id
            )
            move_lines = self.env["account.move.line"].search(
                self._get_journal_items_domain() + [("tax_tag_ids", "in", tags.ids)]
            )
            for move_line in move_lines:
                partner = move_line.move_id.commercial_partner_id
                partner_amounts = amounts.setdefault(
                    partner, {"amount_products": 0.0, "amount_services": 0.0}
                )
                for tag in move_line.tax_tag_ids & tags:
                    partner_amounts[amount_field] += self._get_tag_balance(
                        tag, move_line.tax_tag_invert, move_line.balance
                    )
        return amounts

    def _update_lines(self):
        res = super()._update_lines()
        zm_line_model = self.env["l10n.de.tax.statement.zm.line"]
        for statement in self:
            if not statement.date_from:
                continue
            statement.zm_line_ids = [Command.clear()] + [
                Command.create(zm_line_model._prepare_vals(partner, partner_amounts))
                for partner, partner_amounts in statement._get_zm_amounts().items()
            ]
        return res

    def _get_lines_snapshot(self):
        return super()._get_lines_snapshot() + sorted(
            (
                line.partner_id.id,
                line.vat or "",
                line.country_code or "",
                line.amount_products,
                line.amount_services,
            )
            for line in self.zm_line_ids
        )

    def _check_approve(self):
        res = super()._check_approve()
        # the VAT numbers and countries of the ZM lines
        self._get_zm_rows()
        return res

    def _get_upload_attachments(self):
        attachments = super()._get_upload_attachments()
        if self.zm_line_ids:
            attachments |= self._create_zm_csv_attachment()
        return attachments

    def _round_zm_amount(self, x, n=0):
        try:
            return int(x / abs(x) * int(abs(x) * 10**n + 0.5) / 10**n)
        except ZeroDivisionError:
            return 0

    def _get_zm_rows(self):
        """Return the rows of the ZM: the VAT number, the amount in whole euros
        and the kind (L for products, S for services) of every customer"""
        self.ensure_one()
        self.zm_line_ids._check_country_code()
        res = {}
        for zml in self.zm_line_ids:
            if not zml.vat:
                raise UserError(
                    self.env._(
                        "Partner %(partner)s has no VAT number!",
                        partner=zml.partner_id.name,
                    )
                )
            vat = zml.vat.replace(" ", "").replace("-", "")
            if vat not in res:
                res[vat] = {
                    "amount_products": zml.amount_products,
                    "amount_services": zml.amount_services,
                }
            else:
                res[vat]["amount_products"] += zml.amount_products
                res[vat]["amount_services"] += zml.amount_services
        rows = []
        for vat, amounts in res.items():
            amount_products = self._round_zm_amount(amounts["amount_products"])
            if amount_products:
                rows.append((vat, amount_products, "L"))
            amount_services = self._round_zm_amount(amounts["amount_services"])
            if amount_services:
                rows.append((vat, amount_services, "S"))
        return rows

    def _generate_zm_download_lines(self):
        self.ensure_one()
        return [
            ["#v3.0"],
            ["#ve3.2.1"],
            [
                "Umsatzsteuer-Identifikationsnummer (USt-IdNr.)",
                "Summe (Euro)",
                "Art der Leistung",
            ],
        ] + [list(row) for row in self._get_zm_rows()]

    def _create_zm_csv_attachment(self):
        """Attach the ZM as CSV file for the upload to the BZSt"""
        self.ensure_one()
        zm_download = "\n".join(
            ",".join(str(i) for i in line)
            for line in self._generate_zm_download_lines()
        )
        return self.env["ir.attachment"].create(
            {
                "name": f"ZM_{self.year}_{self.period}.csv",
                "raw": zm_download.encode(),
                "mimetype": "text/csv",
                "res_model": self._name,
                "res_id": self.id,
            }
        )
