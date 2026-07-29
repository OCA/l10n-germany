# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import re

from odoo.addons.base.tests.common import BaseCommon


class TestDin5008SaleMoveName(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.external_report_layout_id = cls.env.ref(
            "l10n_din5008.report_layout_din5008"
        ).view_id

        cls.customer = cls.env["res.partner"].create(
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
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    (0, 0, {"product_id": cls.consulting.id, "product_uom_qty": 1})
                ],
            }
        )

    def _render(self, context=None):
        report = self.env["ir.actions.report"].with_context(**(context or {}))
        html, _ = report._render_qweb_html("sale.report_saleorder", self.sale_order.ids)
        return str(html)

    def _assert_name_after_title(self, html, title):
        expected = (
            re.escape(title)
            + r"\\n\s*</span>\s*\\n\s*<span>\s*\\n\s*"
            + re.escape(self.sale_order.name)
        )
        self.assertRegex(html, expected)

    def test_name_quotation(self):
        """Test the name is shown on a quotation"""
        self.assertIn(self.sale_order.state, ("draft", "sent"))
        html = self._render()
        self._assert_name_after_title(html, "Quotation")

    def test_name_sales_order(self):
        """Test the name is shown on a confirmed sales order"""
        self.sale_order.action_confirm()
        html = self._render()
        self._assert_name_after_title(html, "Sales Order")

    def test_name_proforma(self):
        """Test the name is shown on a pro forma invoice"""
        html = self._render(context={"proforma": True})
        self._assert_name_after_title(html, "Pro Forma Invoice")
