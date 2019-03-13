# Copyright 2018 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_de_tax_statement.tests.test_l10n_de_tax_statement\
    import TestVatStatement


class TestTaxStatementZM(TestVatStatement):

    def _prepare_zm_invoice(self):
        for invoice_line in self.invoice_1.invoice_line_ids:
            for tax_line in invoice_line.invoice_line_tax_ids:
                tax_line.tag_ids = self.tag_3
        self.invoice_1._onchange_invoice_line_ids()
        self.invoice_1.action_invoice_open()
        self.statement_with_zm.statement_update()

    def test_01_compute_tag_41(self):
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.assertEqual(self.statement_with_zm.tag_41_base, self.tag_3)
        self.assertEqual(self.statement_with_zm.tag_21_base, self.tag_4)

    def test_02_no_tag_41(self):
        self.config.write({
            'tag_41_base': False,
            'tag_21_base': False,
        })
        self.statement_not_valid = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })
        self.statement_not_valid.statement_update()
        with self.assertRaises(UserError):
            self.statement_not_valid.post()

    def test_03_post_final(self):
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        # all previous statements must be already posted
        self.statement_with_zm.statement_update()
        with self.assertRaises(UserError):
            self.statement_with_zm.post()

        self.statement_1.statement_update()
        self.statement_1.post()
        self.assertEqual(self.statement_1.state, 'posted')

        # first post
        self.statement_with_zm.post()

        self.assertEqual(self.statement_with_zm.state, 'posted')
        self.assertTrue(self.statement_with_zm.date_posted)

        self.statement_with_zm.zm_update()

        # then finalize
        self.statement_with_zm.finalize()
        self.assertEqual(self.statement_with_zm.state, 'final')
        self.assertTrue(self.statement_with_zm.date_posted)

        with self.assertRaises(UserError):
            self.statement_with_zm.zm_update()

    def test_04_zm_invoice(self):
        self.statement_1.post()
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.invoice_1.partner_id.country_id = self.env.ref('base.be')
        self._prepare_zm_invoice()

        self.statement_with_zm.post()
        self.assertTrue(self.statement_with_zm.zm_line_ids)
        self.assertTrue(self.statement_with_zm.zm_total)

        for zm_line in self.statement_with_zm.zm_line_ids:
            self.assertTrue(zm_line.amount_products)
            self.assertFalse(zm_line.amount_services)
            amount_products = zm_line.format_amount_products
            self.assertEqual(float(amount_products), zm_line.amount_products)
            amount_services = zm_line.format_amount_services
            self.assertEqual(float(amount_services), zm_line.amount_services)

    def test_05_zm_invoice_service(self):
        self.statement_1.post()
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.invoice_1.partner_id.country_id = self.env.ref('base.be')
        for invoice_line in self.invoice_1.invoice_line_ids:
            for tax_line in invoice_line.invoice_line_tax_ids:
                tax_line.tag_ids = self.tag_4
        self.invoice_1._onchange_invoice_line_ids()
        self.invoice_1.action_invoice_open()
        self.statement_with_zm.statement_update()

        self.statement_with_zm.post()
        self.assertTrue(self.statement_with_zm.zm_line_ids)
        self.assertTrue(self.statement_with_zm.zm_total)

        for zm_line in self.statement_with_zm.zm_line_ids:
            self.assertFalse(zm_line.amount_products)
            self.assertTrue(zm_line.amount_services)
            amount_products = zm_line.format_amount_products
            self.assertEqual(float(amount_products), zm_line.amount_products)
            amount_services = zm_line.format_amount_services
            self.assertEqual(float(amount_services), zm_line.amount_services)

    def test_06_zm_invoice_de(self):
        self.statement_1.post()
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.invoice_1.partner_id.country_id = self.env.ref('base.de')
        self._prepare_zm_invoice()

        with self.assertRaises(ValidationError):
            self.statement_with_zm.post()

    def test_07_zm_invoice_outside_europe(self):
        self.statement_1.post()
        self.statement_with_zm = self.env['l10n.de.tax.statement'].create({
            'name': 'Statement 1',
        })

        self.invoice_1.partner_id.country_id = self.env.ref('base.us')
        self._prepare_zm_invoice()

        with self.assertRaises(ValidationError):
            self.statement_with_zm.post()
