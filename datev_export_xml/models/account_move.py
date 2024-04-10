# Copyright (C) 2022-2023 initOS GmbH
# Copyright (C) 2019 sewisoft (sewisoft.de)
# Copyright (C) 2010-2023 big-consulting GmbH (www.openbig.de)
# Copyright (C) 2010 OpenGLOBE Grzegorz Grzelak (www.openglobe.pl)
# @author Guenter Selbert <guenter.selbert@sewisoft.de>
# @author Thorsten Vocks
# @author Grzegorz Grzelak
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def datev_price_information(self):
        self.ensure_one()
        return self.tax_ids.compute_all(
            self.price_unit * (1 - (self.discount / 100.0)),
            self.currency_id,
            self.quantity,
            product=self.product_id,
            partner=self.move_id.partner_id,
        )


class AccountMove(models.Model):
    _inherit = "account.move"

    datev_exported = fields.Boolean(
        string="Exported to Datev",
        copy=False,
        help="When finishing a datev export the processed invoices are marked as exported.\n"
        "If you need to export the invoices again, set this field to False.",
    )
    datev_validation = fields.Text()

    def datev_format_total(self, value, prec=2):
        self.ensure_one()
        return (
            f"{-value:.{prec}f}"
            if self.move_type.endswith("_refund")
            else f"{value:.{prec}f}"
        )

    def datev_sanitize(self, value, length=36):
        return re.sub(r"[^a-zA-Z0-9$%&\*\+\-/]", "-", value)[:length]

    def datev_filename(self, extension=".pdf"):
        self.ensure_one()
        return self.name.replace("/", "-") + extension

    def datev_delivery_date(self):
        self.ensure_one()
        if "stock.move" not in self.env:
            _logger.info("Invoice date used as delivery date.")
            return self.invoice_date

        pickings = self.env["stock.move"]
        if self.move_type == "out_invoice":
            pickings = self.mapped("invoice_line_ids.sale_line_ids.move_ids.picking_id")
        elif self.move_type == "in_invoice":
            pickings = self.mapped("invoice_line_ids.purchase_order_id.picking_ids")

        if pickings:
            return pickings.sorted("date", reverse=True)[0].date.date()

        _logger.info("Invoice date used as delivery date.")
        return self.invoice_date

    def datev_invoice_type(self):
        self.ensure_one()
        if self.move_type in ["out_invoice", "in_invoice"]:
            return "Rechnung"
        return "Gutschrift/Rechnungskorrektur"

    def datev_invoice_id(self):
        self.ensure_one()
        return self.datev_sanitize(self.name or "")

    def datev_order_id(self):
        self.ensure_one()
        origin = self.invoice_origin or ""
        if self.move_type not in (
            "in_invoice",
            "in_refund",
            "out_invoice",
            "out_refund",
        ):
            return self.datev_sanitize(origin)

        # Use the correct setting
        if self.move_type.startswith("in_"):
            ref_field = self.sudo().company_id.datev_vendor_order_ref
        else:
            ref_field = self.sudo().company_id.datev_customer_order_ref

        # Show the original move because ref is a combined value for refund
        if ref_field == "partner" and self.move_type.endswith("_refund"):
            return self.datev_sanitize(self.reversed_entry_id.name or origin)

        # Show the partner reference from the orders stored in ref
        if ref_field == "partner":
            return self.datev_sanitize(self.ref or origin)

        # Show the payment reference
        if ref_field == "payment":
            return self.datev_sanitize(self.payment_reference or origin)

        return self.datev_sanitize(origin)
