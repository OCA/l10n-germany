# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestDin5008StockPickingTypeName(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.external_report_layout_id = cls.env.ref(
            "l10n_din5008.report_layout_din5008"
        ).view_id
        cls.JournalObj = cls.env["account.journal"]
        cls.sale_journal = cls.JournalObj.search(
            [
                ("type", "=", "sale"),
                ("company_id", "=", cls.company.id),
            ],
            limit=1,
        )
        if not cls.sale_journal:
            cls.sale_journal = cls.JournalObj.create(
                {
                    "name": "Test sale journal",
                    "code": "sale",
                    "type": "sale",
                    "company_id": cls.company.id,
                }
            )
        cls.InvoiceObj = cls.env["account.move"]

        cls.customer_de = cls.env["res.partner"].create(
            {
                "name": "Test customer",
            }
        )

        cls.consulting = cls.env["product.product"].create(
            {
                "name": "Test consulting",
                "list_price": 100.0,
                "standard_price": 50.0,
            }
        )

        cls.picking_type_out = cls.env.ref("stock.warehouse0").out_type_id
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.customer_de.id,
                "picking_type_id": cls.picking_type_out.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.consulting.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )

    def _render(self, report_name, records):
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            report_name, records.ids
        )
        return html.decode()

    def _subject(self, html):
        """Return the DIN 5008 layout subject line.

        The layout renders it in a bare <h2>, before the document body. The
        delivery slip body has an <h2 style="..."> of its own, which already
        shows the picking type name, so the tests must not look at it.
        """
        return re.search(r"<h2>(.*?)</h2>", html, re.DOTALL).group(1)

    def test_picking_type_name(self):
        """Test the subject line of a delivery slip"""
        subject = self._subject(self._render("stock.report_deliveryslip", self.picking))
        expected = (
            r"<span>\s*"
            + re.escape(self.picking_type_out._get_code_report_name())
            + r"\s*</span>\s*<span>\s*"
            + re.escape(self.picking.name)
        )
        self.assertRegex(subject, expected)

    def test_invoice_title(self):
        """Test that the subject line of an invoice is left untouched"""
        invoice = self.InvoiceObj.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.customer_de.id,
                "journal_id": self.sale_journal.id,
                "invoice_line_ids": [
                    Command.create({"product_id": self.consulting.id, "quantity": 1})
                ],
            }
        )
        invoice.action_post()
        subject = self._subject(
            self._render("account.report_invoice_with_payments", invoice)
        )
        # account.move sets din5008_document_title, so the replaced t-elif
        # branch must not contribute anything to the subject line. Other addons
        # of this repo may add to it, so only assert on what this addon owns.
        self.assertIn("Invoice", subject)
        self.assertNotIn(self.picking_type_out._get_code_report_name(), subject)
