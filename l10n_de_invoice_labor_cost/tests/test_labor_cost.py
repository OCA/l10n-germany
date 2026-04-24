# Copyright 2025 Maik Derstappen (https://derico.de)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestLaborCostProduct(BaseCommon):
    """Tests for labor cost product functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.labor_product = cls.env["product.product"].create(
            {
                "name": "Test Labor Service",
                "type": "service",
                "list_price": 100.0,
                "is_labor_cost_product": True,
            }
        )
        cls.labor_product_2 = cls.env["product.product"].create(
            {
                "name": "Test Labor Service 2",
                "type": "service",
                "list_price": 50.0,
                "is_labor_cost_product": True,
            }
        )
        cls.service_product = cls.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
                "list_price": 100.0,
            }
        )
        cls.consu_product = cls.env["product.product"].create(
            {
                "name": "Test Consumable",
                "type": "consu",
                "list_price": 50.0,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def test_01_labor_cost_product_flag(self):
        """Test that labor cost product flag can be set on service products."""
        self.service_product.is_labor_cost_product = True
        self.assertTrue(self.service_product.is_labor_cost_product)

    def test_02_labor_cost_product_consu_restriction(self):
        """Test that labor cost flag cannot be set on consumable products."""
        with self.assertRaises(ValidationError):
            self.consu_product.is_labor_cost_product = True

        with self.assertRaises(ValidationError):
            self.labor_product.type = "consu"

    def test_03_invoice_labor_cost_calculation(self):
        """Test that labor cost values are calculated on invoices."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.labor_product.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    ),
                ],
            }
        )
        invoice._compute_labor_cost_values()

        self.assertEqual(invoice.l10n_de_labor_cost_net, 100.0)
        self.assertGreaterEqual(
            invoice.l10n_de_labor_cost_gross, invoice.l10n_de_labor_cost_net
        )
        expected_tax = invoice.l10n_de_labor_cost_gross - invoice.l10n_de_labor_cost_net
        self.assertEqual(invoice.l10n_de_labor_cost_tax, expected_tax)

    def test_04_invoice_mixed_products(self):
        """Test invoice with both labor cost and regular products."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.labor_product.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.consu_product.id,
                            "quantity": 1,
                            "price_unit": 50.0,
                        },
                    ),
                ],
            }
        )
        invoice._compute_labor_cost_values()

        self.assertEqual(invoice.l10n_de_labor_cost_net, 100.0)
        self.assertGreaterEqual(invoice.l10n_de_labor_cost_gross, 100.0)

    def test_05_invoice_no_labor_cost(self):
        """Test invoice without labor cost products."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.consu_product.id,
                            "quantity": 2,
                            "price_unit": 50.0,
                        },
                    ),
                ],
            }
        )
        invoice._compute_labor_cost_values()
        self.assertEqual(invoice.l10n_de_labor_cost_net, 0.0)
        self.assertEqual(invoice.l10n_de_labor_cost_tax, 0.0)
        self.assertEqual(invoice.l10n_de_labor_cost_gross, 0.0)

    def test_06_invoice_multiple_labor_lines(self):
        """Test invoice with multiple labor cost lines."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.labor_product.id,
                            "quantity": 2,
                            "price_unit": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.labor_product_2.id,
                            "quantity": 1,
                            "price_unit": 50.0,
                        },
                    ),
                ],
            }
        )

        invoice._compute_labor_cost_values()

        self.assertEqual(invoice.l10n_de_labor_cost_net, 250.0)
        self.assertGreaterEqual(invoice.l10n_de_labor_cost_gross, 250.0)
